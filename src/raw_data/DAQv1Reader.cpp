#include <shm_raw.hpp>
#include "DAQv1Reader.hpp"

#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <assert.h>
#include <ctype.h>
#include <fstream>
#include <iostream>


using namespace std;
using namespace PETSYS;

static unsigned ELINK_MAP(unsigned n)
{
	switch (n) {
		case  9: return 5;
		case 10: return 4;
		case 11: return 3;
		case 12: return 2;
		case 13: return 1;
		case 14: return 0;
		case 15: return 5;
		case 16: return 4;
		case 17: return 3;
		case 18: return 2;
		case 19: return 1;
		case 20: return 0;
		default: return -1;
	}
}

static const unsigned long long timetag_period = 1ULL<<32;
static const unsigned long long timetag_half_period = timetag_period / 2;


DAQv1Reader::DAQv1Reader() :
	dataFile(NULL)

{
}

DAQv1Reader::~DAQv1Reader()
{
	fclose(dataFile);
}

DAQv1Reader *DAQv1Reader::openFile(const char *fName, FILE *decoder_log)
{
	FILE * rawFile = fopen(fName, "r");
	if(rawFile == NULL) {
		fprintf(stderr, "Could not open '%s' for reading: %s\n", fName, strerror(errno));
                exit(1);
	}

	DAQv1Reader *reader = new DAQv1Reader();
	reader->dataFile = rawFile;
	reader->decoder_log = decoder_log;

	return reader;
}

int DAQv1Reader::getNSteps()
{
	return 1;
}

double DAQv1Reader::getFrequency()
{
	return 160E6;
}

bool DAQv1Reader::isQDC()
{
	return 0;
}

void DAQv1Reader::getStepValue(int n, float &step1, float &step2)
{
	step1 = 0;
	step2 = 0;
}

void DAQv1Reader::readThrValues(char* inputFilePrefix, float& step1, float& step2)
{
  std::string inputFilePrefixString(inputFilePrefix);
  std::size_t lastindex = inputFilePrefixString.find_last_of(".");
  std::string rawname = inputFilePrefixString.substr(0, lastindex);
  rawname += ".txt";
  std::ifstream inFile(rawname.c_str());

  float vth1, vth2, vthe;
  while (true) {
    inFile >> vth1 >> vth2 >> vthe;
    if(inFile.eof())
      {
        break;
      }
  }

  step1=vth1;
  step2=vth2;
  return;
}

static unsigned __int128 hex_to_u128(char *s)
{

	unsigned __int128 result = 0;
	
	for(int k = 0; k < strlen(s); k++) {
		result = result << 4;
		switch(toupper(s[k])) {
			case '0': result |= 0x0; break;
			case '1': result |= 0x1; break;
			case '2': result |= 0x2; break;
			case '3': result |= 0x3; break;
			case '4': result |= 0x4; break;
			case '5': result |= 0x5; break;
			case '6': result |= 0x6; break;
			case '7': result |= 0x7; break;
			case '8': result |= 0x8; break;
			case '9': result |= 0x9; break;
			case 'A': result |= 0xA; break;
			case 'B': result |= 0xB; break;
			case 'C': result |= 0xC; break;
			case 'D': result |= 0xD; break;
			case 'E': result |= 0xE; break;
			case 'F': result |= 0xF; break;
			default: break;
		}
	}
	return result;
}


void DAQv1Reader::processStep(int n, bool verbose, EventSink<RawHit> *sink)
{
	
	sink->pushT0(0);
	int nEvents = 0;
	
	RawDataFrame *dataFrame = new RawDataFrame;

	int64_t first_elink_id = -1;
	int64_t first_rx_timetag = 0;
	int64_t last_rx_timetag = 0;
	int64_t rx_timetag_wraps = 0;
	uint64_t outBufferMinTime = 0;
	uint64_t outBufferMaxTime = 0;
	const long outBlockSize = 4*1024;
	EventBuffer<RawHit> *outBuffer = new EventBuffer<RawHit>(outBlockSize, outBufferMinTime);; 
	
	char *text_line = new char[256];
	size_t text_length;
	while(getline(&text_line, &text_length, dataFile) > 0) {
//		if( decoder_log ) fprintf(decoder_log, "line = '%s'\n", text_line);
		unsigned link;
		unsigned elink;
		unsigned event_number;
		char tt_hex[256];
		char evt_hex[256];
		int r = sscanf(text_line, "%u; %u; %u;0x%[0-9a-f]; 0x%[0-9a-f]L\n", &link, &elink, &event_number, tt_hex, evt_hex);
 		if (r != 5) continue;
 		
		uint64_t rx_timetag = hex_to_u128(tt_hex) % timetag_period;
		unsigned __int128 evt = hex_to_u128(evt_hex) >> 32;
		
		unsigned evt_type = (evt >> 87) & 0x1;
		if(decoder_log != NULL) fprintf(decoder_log, "%3d %3d %3d '%12s' '%32s'", link, elink, event_number, tt_hex, evt_hex);
		
		if(evt_type != 0) {
			if(decoder_log != NULL) fprintf(decoder_log, " BAD\n");
			continue;
		}

		// We don't know this ELINK ID
		if(ELINK_MAP(elink) == -1) {
			if(decoder_log != NULL) fprintf(decoder_log, " UNKNOWN ELINK\n");
			continue;
		}

		// Detect wrap around of rx_timetag
		// TODO: rx_timetag may also be reset but there's no other way to handle it
		// so we treat it as a wrap around
		// WARNING: Data comes batched by elink and thus a single wrap could be detected multiple times
		// Only data from the elink of the first event is considered for timetag wrap-around detection
		bool wraparound = false;
		int64_t  elink_id2 = (link << 8) | elink;
		if(first_elink_id == -1) {
			// This is the first event in the data
			first_elink_id = elink_id2;
			first_rx_timetag = rx_timetag;
			last_rx_timetag = rx_timetag;
			rx_timetag_wraps = 0;
		}
		else if(elink_id2 == first_elink_id) {
			if((rx_timetag & timetag_half_period) < (last_rx_timetag & timetag_half_period)) {
				rx_timetag_wraps += 1;
				wraparound = true;
			}
			last_rx_timetag = rx_timetag;
		}

		// Construct an absolute rx_timeag relative to the first rx_timetag in the data
		int64_t rx_timetag2 = rx_timetag + rx_timetag_wraps * timetag_period - first_rx_timetag;

		// Construct an absolute event time tag
		// First decode the event coarse time information
		unsigned t1coarse = ((evt >> 73) & 0x3FFF);
		unsigned t2coarse	= ((evt >> 63) % 1024);
		unsigned qcoarse	= ((evt >> 53) % 1024);
		unsigned pcoarse	= ((evt >> 13) % 1024);

		int64_t absoluteT1 = (rx_timetag2 & 0xFFFFFFFFFFFFE000ULL) | t1coarse;
		// Correct wrap-around of t1coarse
		if(absoluteT1 < rx_timetag2) absoluteT1 += 0x10000;

		if(absoluteT1 > outBufferMaxTime) outBufferMaxTime = absoluteT1;
		outBuffer->setTMax(outBufferMaxTime);

                if((outBuffer->getSize() + 1 > outBlockSize) || ((outBufferMaxTime - outBufferMinTime) > 1099511627776ULL)) {
                        sink->pushEvents(outBuffer);
                        outBufferMinTime = outBufferMaxTime;
                        outBuffer = new EventBuffer<RawHit>(outBlockSize, outBufferMinTime);
                }
		RawHit &e = outBuffer->getWriteSlot();
		
		// Match FEB/D data behaviour
		// frameID is the most significant bits of the absolute time tag
		uint64_t frameID = absoluteT1 >> 10;
		e.channelID	= (link << 12) | (ELINK_MAP(elink) << 6) | ((evt >> 0) % 32);
		e.tacID		= ((evt >> 5) % 8);
		e.t1fine	= ((evt >> 23) % 1024);
		e.t2fine	= ((evt >> 33) % 1024);
		e.qfine		= ((evt >> 43) % 1024);
		e.prevEventFlags= ((evt >> 8) % 16);

		long long t1 = (frameID << 10) | t1coarse;
		long long t2 = (t1 & 0x7FFFFFFFFFFFFC00LL) | t2coarse;
		long long tq = (t1 & 0x7FFFFFFFFFFFFC00LL) | qcoarse;
		long long tp = (t1 & 0x7FFFFFFFFFFFF000LL) | (pcoarse << 2);

		if(t2 < t1) t2 += 1024;
		if(tq < t1) tq += 1024;
		if(tp >= t1) tp -= 4096;

		e.time = t1 - outBufferMinTime;
		e.timeEnd = t2 - outBufferMinTime;
		e.timeEndQ = tq - outBufferMinTime;
		e.prevEventTime = tp - outBufferMinTime;

		e.valid = true;

		
		if(decoder_log != NULL) {
			fprintf(decoder_log, " GOOD ");
			fprintf(decoder_log, ": %14lld %4lld%c %14lld %5hu %20lld %15.12g", rx_timetag, rx_timetag_wraps, wraparound ? 'W' : ' ', rx_timetag2, t1coarse, absoluteT1, absoluteT1 / getFrequency() );
			fprintf(decoder_log, ": %2hu %2hu %1hu : %6hu %4hu %4hu; %4hu %4hu %4hu", e.channelID / 64, e.channelID % 64, e.tacID, t1coarse % 1024, t2coarse, qcoarse, e.t1fine, e.t2fine, e.qfine);
			fprintf(decoder_log, "\n");
		}
		e.valid = true;

		outBuffer->pushWriteSlot();
		nEvents += 1;
		
		
		
	}
	delete [] text_line;
	
	sink->pushEvents(outBuffer);
	outBuffer = NULL;
	
	sink->finish();
	if(verbose) {
		fprintf(stderr, "DAQv1Reader report\n");
		fprintf(stderr, " events\n");
		fprintf(stderr, " %10lld total\n", nEvents);
		sink->report();
	}
	
	delete dataFrame;
	delete sink;
	
}
