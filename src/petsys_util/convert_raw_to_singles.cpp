#include <RawReader.hpp>
#include <DAQv1Reader.hpp>
#include <OverlappedEventHandler.hpp>
#include <getopt.h>
#include <assert.h>
#include <SystemConfig.hpp>
#include <CoarseSorter.hpp>
#include <ProcessHit.hpp>
#include <SimpleGrouper.hpp>
#include <CoincidenceGrouper.hpp>

#include <boost/lexical_cast.hpp>

#include <TFile.h>
#include <TTree.h>

using namespace PETSYS;

enum FILE_TYPE { FILE_TEXT, FILE_BINARY, FILE_ROOT };

class DataFileWriter {
private:
	double frequency;
	FILE_TYPE fileType;
	int eventFractionToWrite;
	long long eventCounter;

	FILE *dataFile;
	FILE *indexFile;
	off_t stepBegin;
	
	TTree *hData;
	TTree *hIndex;
	TFile *hFile;
	// ROOT Tree fields
	float		brStep1;
	float		brStep2;
	long long 	brStepBegin;
	long long 	brStepEnd;

	long long	brTime;
	unsigned int	brChannelID;
	float		brToT;
        float           brT1Coarse;
        float           brT1Fine;
        float           brT2Coarse;
        float           brT2Fine;
        float           brQCoarse;
        float           brQFine;
	float		brEnergy;
	float		brQT1;
	float		brQT2;
	unsigned short	brTacID;
	int		brXi;
	int		brYi;
	float		brX;
	float 		brY;
	float 		brZ;
	float		brTQT;
	float		brTQE;
	long long	brPrevEventTime;
	unsigned short	brPrevEventFlags;
	

	struct Event {
		long long time;
		float e;
		int id;  
	} __attribute__((__packed__));
	
public:
	DataFileWriter(char *fName, double frequency, FILE_TYPE fileType, int eventFractionToWrite) {
		this->frequency = frequency;
		this->fileType = fileType;
		this->eventFractionToWrite = eventFractionToWrite;
		this->eventCounter = 0;

		stepBegin = 0;
		
		if (fileType == FILE_ROOT){
			hFile = new TFile(fName, "RECREATE");
			int bs = 512*1024;

			hData = new TTree("data", "Event List", 2);
			hData->Branch("step1", &brStep1, bs);
			hData->Branch("step2", &brStep2, bs);
			hData->Branch("time", &brTime, bs);
			hData->Branch("channelID", &brChannelID, bs);
			hData->Branch("tot", &brToT, bs);
			hData->Branch("t1coarse", &brT1Coarse, bs);
			hData->Branch("t1fine", &brT1Fine, bs);
			hData->Branch("t2coarse", &brT2Coarse, bs);
			hData->Branch("t2fine", &brT2Fine, bs);
			hData->Branch("qcoarse", &brQCoarse, bs);
			hData->Branch("qfine", &brQFine, bs);
			hData->Branch("energy", &brEnergy, bs);
			hData->Branch("qT1", &brQT1, bs);
			hData->Branch("qT2", &brQT2, bs);
			hData->Branch("tacID", &brTacID, bs);
			hData->Branch("xi", &brXi, bs);
			hData->Branch("yi", &brYi, bs);
			hData->Branch("x", &brX, bs);
			hData->Branch("y", &brY, bs);
			hData->Branch("z", &brZ, bs);
			hData->Branch("tqT", &brTQT, bs);
			hData->Branch("tqE", &brTQE, bs);
			hData->Branch("prevEventTime", &brPrevEventTime, bs);
			hData->Branch("prevEventFlags", &brPrevEventFlags, bs);
			
			hIndex = new TTree("index", "Step Index", 2);
			hIndex->Branch("step1", &brStep1, bs);
			hIndex->Branch("step2", &brStep2, bs);
			hIndex->Branch("stepBegin", &brStepBegin, bs);
			hIndex->Branch("stepEnd", &brStepEnd, bs);
		}
		else if(fileType == FILE_BINARY) {
			char fName2[1024];
			sprintf(fName2, "%s.ldat", fName);
			dataFile = fopen(fName2, "w");
			sprintf(fName2, "%s.lidx", fName);
			indexFile = fopen(fName2, "w");
			assert(dataFile != NULL);
			assert(indexFile != NULL);
		}
		else {
			dataFile = fopen(fName, "w");
			assert(dataFile != NULL);
			indexFile = NULL;
		}
	};
	
	~DataFileWriter() {
		if (fileType == FILE_ROOT){
			hFile->Write();
			hFile->Close();
		}
		else if(fileType == FILE_BINARY) {
			fclose(dataFile);
			fclose(indexFile);
		}
		else {
			fclose(dataFile);
		}
	}
	
	void closeStep(float step1, float step2) {
		if (fileType == FILE_ROOT){
			brStepBegin = stepBegin;
			brStepEnd = hData->GetEntries();
			brStep1 = step1;
			brStep2 = step2;
			hIndex->Fill();
			stepBegin = hData->GetEntries();
		}
		else if(fileType == FILE_BINARY) {
			fprintf(indexFile, "%llu\t%llu\t%e\t%e\n", stepBegin, ftell(dataFile), step1, step2);
			stepBegin = ftell(dataFile);
		}
		else {
			// Do nothing
		}
	};
	
	void addEvents(float step1, float step2,EventBuffer<Hit> *buffer) {
		double Tps = 1E12/frequency;
		float Tns = Tps / 1000;
				
		long long tMin = buffer->getTMin() * (long long)Tps;
		
		int N = buffer->getSize();
		for (int i = 0; i < N; i++) {
			long long tmpCounter = eventCounter;
			eventCounter += 1;
			if((tmpCounter % 1024) >= eventFractionToWrite) continue;

			Hit &hit = buffer->get(i);
			if(!hit.valid) continue;

			float Eunit = 1.0;
			
			if (fileType == FILE_ROOT){
				brStep1 = step1;
				brStep2 = step2;
				
				brTime = ((long long)(hit.time * Tps)) + tMin;
				brChannelID = hit.raw->channelID;
				brToT = (hit.timeEnd - hit.time) * Tps;
                                brT1Coarse = hit.raw->time & 0x1FFF;
                                brT1Fine = hit.raw->t1fine;
                                brT2Coarse = hit.raw->timeEnd & 0x3FF;
                                brT2Fine = hit.raw->t2fine;
                                brQCoarse = hit.raw->timeEndQ & 0x3FF;
                                brQFine = hit.raw->qfine;
				brEnergy = hit.energy * Eunit;
                                brQT1 = hit.qT1;
                                brQT2 = hit.qT2;
				brTacID = hit.raw->tacID;
				brTQT = hit.raw->time - hit.time;
				brTQE = (hit.raw->timeEnd - hit.timeEnd);
				brX = hit.x;
				brY = hit.y;
				brZ = hit.z;
				brXi = hit.xi;
				brYi = hit.yi;
				brPrevEventTime = ((long long)((hit.raw->time - hit.raw->prevEventTime) * Tps));
				brPrevEventFlags = hit.raw->prevEventFlags;
				
				hData->Fill();
			}
			else if(fileType == FILE_BINARY) {
				Event eo = {
					((long long)(hit.time * Tps)) + tMin,
					hit.energy * Eunit,
					(int)hit.raw->channelID
				};
				fwrite(&eo, sizeof(eo), 1, dataFile);
			}
			else {
				fprintf(dataFile, "%lld\t%f\t%d\n",
					((long long)(hit.time * Tps)) + tMin,
					hit.energy * Eunit,
					(int)hit.raw->channelID
					);
			}
		}
		
	}
	
};

class WriteHelper : public OverlappedEventHandler<Hit, Hit> {
private: 
	DataFileWriter *dataFileWriter;
	float step1;
	float step2;
public:
	WriteHelper(DataFileWriter *dataFileWriter, float step1, float step2, EventSink<Hit> *sink) :
		OverlappedEventHandler<Hit, Hit>(sink, true),
		dataFileWriter(dataFileWriter), step1(step1), step2(step2)
	{
	};
	
	EventBuffer<Hit> * handleEvents(EventBuffer<Hit> *buffer) {
		dataFileWriter->addEvents(step1, step2,buffer);
		return buffer;
	};
	
	void pushT0(double t0) { };
	void report() { };
};

void displayHelp(char * program)
{
	fprintf(stderr, "Usage: %s --config <config_file> -i <input_file_prefix> -o <output_file_prefix> [optional arguments]\n", program);
	fprintf(stderr, "Arguments:\n");
	fprintf(stderr,  "  --config \t\t Configuration file containing path to tdc calibration table \n");
	fprintf(stderr,  "  -i \t\t\t Input file prefix - raw data\n");
	fprintf(stderr,  "  -o \t\t\t Output file name - by default in text dataformat\n");
	fprintf(stderr, "Optional flags:\n");
	fprintf(stderr,  "  --writeBinary \t Set the output data format to binary\n");
	fprintf(stderr,  "  --writeRoot \t\t Set the output data format to ROOT TTree\n");
	fprintf(stderr,  "  --writeFraction N \t\t Fraction of events to write. Default: 100%.\n");
	fprintf(stderr,  "  --daqv1 \t\t Parse DAQv1 data.\n");
	fprintf(stderr,  "  --att  \t\t  Attenuator gain setting. Default: 4\n");
	fprintf(stderr,  "  --help \t\t Show this help message and exit \n");	
	
};

void displayUsage(char *argv0)
{
	printf("Usage: %s --config <config_file> -i <input_file_prefix> -o <output_file_prefix> [optional arguments]\n", argv0);
}

int main(int argc, char *argv[])
{
	char *configFileName = NULL;
        char *inputFilePrefix = NULL;
        char *outputFileName = NULL;
	FILE_TYPE fileType = FILE_TEXT;
	long long eventFractionToWrite = 1024;
	int parser_type = 0;
	int att = 4;


        static struct option longOptions[] = {
                { "help", no_argument, 0, 0 },
                { "config", required_argument, 0, 0 },
		{ "writeBinary", no_argument, 0, 0 },
		{ "writeRoot", no_argument, 0, 0 },
		{ "writeFraction", required_argument },
		{ "daqv1", no_argument, 0, 0 },
		{ "att", required_argument, 0, 0 }
        };

        while(true) {
                int optionIndex = 0;
                int c = getopt_long(argc, argv, "i:o:c:",longOptions, &optionIndex);

                if(c == -1) break;
                else if(c != 0) {
                        // Short arguments
                        switch(c) {
                        case 'i':       inputFilePrefix = optarg; break;
                        case 'o':       outputFileName = optarg; break;
			default:        displayUsage(argv[0]); exit(1);
			}
		}
		else if(c == 0) {
			switch(optionIndex) {
			case 0:		displayHelp(argv[0]); exit(0); break;
                        case 1:		configFileName = optarg; break;
			case 2:		fileType = FILE_BINARY; break;
			case 3:		fileType = FILE_ROOT; break;
			case 4:		eventFractionToWrite = round(1024 *boost::lexical_cast<float>(optarg) / 100.0); break;
			case 5:		parser_type = 1; break;
			case 6:		att = atoi(optarg); break;

			default:	displayUsage(argv[0]); exit(1);
			}
		}
		else {
			assert(false);
		}
	}

	if(configFileName == NULL) {
		fprintf(stderr, "--config must be specified\n");
		exit(1);
	}
	
	if(inputFilePrefix == NULL) {
		fprintf(stderr, "-i must be specified\n");
		exit(1);
	}

	if(outputFileName == NULL) {
		fprintf(stderr, "-o must be specified\n");
		exit(1);
	}

	AbstractRawReader *reader;
	if( parser_type == 1 ) {
		reader = DAQv1Reader::openFile(inputFilePrefix, NULL);
	}
	else {
		reader = RawReader::openFile(inputFilePrefix);
	}

	
	unsigned long long mask = SystemConfig::LOAD_ALL;
	SystemConfig *config = SystemConfig::fromFile(configFileName, mask, att);
	
	DataFileWriter *dataFileWriter = new DataFileWriter(outputFileName, reader->getFrequency(),  fileType, eventFractionToWrite);
	
	for(int stepIndex = 0; stepIndex < reader->getNSteps(); stepIndex++) {
		float step1, step2;
		reader->getStepValue(stepIndex, step1, step2);
		printf("Processing step %d of %d: (%f, %f)\n", stepIndex+1, reader->getNSteps(), step1, step2);
		fflush(stdout);
		reader->processStep(stepIndex, true,
				new CoarseSorter(
				new ProcessHit(config, reader,
				new WriteHelper(dataFileWriter, step1, step2,
				new NullSink<Hit>()
				))));

		dataFileWriter->closeStep(step1, step2);
	}

	delete dataFileWriter;
	delete reader;

	return 0;
}
