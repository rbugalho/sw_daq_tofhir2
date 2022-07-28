#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <errno.h>
#include <string.h>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <getopt.h>
#include <sys/sysinfo.h>
#include <sys/types.h>
#include <sys/wait.h>

#include <shm_raw.hpp>
using namespace PETSYS;

void displayUsage()
{
}

int main(int argc, char *argv[])
{
	char *input1FilePrefix = NULL;
	bool suppressEmpty = false;
	bool statsOnly = false;
	
	static struct option longOptions[] = {
                { "suppress-empty", no_argument, 0, 0 },
		{ "stats-only", no_argument, 0, 0 }
        };

	while(true) {
		int optionIndex = 0;
                int c = getopt_long(argc, argv, "i:",longOptions, &optionIndex);

		if(c == -1) break;
		else if(c != 0) {
			// Short arguments
			switch(c) {
			case 'i':	input1FilePrefix = optarg; break;
			default:	displayUsage(); exit(1);
			}
		}
		else if(c == 0) {
			switch(optionIndex) {
			case 0: 	suppressEmpty = true ; break;
			case 1:		statsOnly = true; break;
			default:	displayUsage(); exit(1);
			}
		}
		else {
			assert(false);
		}

	}	
	
	char fName[1024];
	// Open the data index file
	sprintf(fName, "%s.idxf", input1FilePrefix);
	FILE *indexFile = fopen(fName, "r");
	if(indexFile == NULL) {
			fprintf(stderr, "Could not open '%s' for reading: %s\n", fName, strerror(errno));
			exit(1);
	}
	
	// Open the data file
	sprintf(fName, "%s.rawf", input1FilePrefix);
	FILE *dataFile = fopen(fName, "r");
	if(dataFile == NULL) {
		fprintf(stderr, "Could not open '%s' for reading: %s\n", fName, strerror(errno));
		exit(1);
	}


	long nEvents0 = 0;
	long nEventsL = 0;
	long nEvents8 = 0;
	long nEventsH = 0;
	long wrongCoarseTime = 0;
	long wrongChannelID = 0;
	long totalDataFrames = 0;
	long totalDataFramesLost = 0;

	unsigned long prevT1 = 0;

	long startOffset, endOffset;
	long long startFrame;
	long long endFrame;
	float step1, step2;
	RawDataFrame *tmpRawDataFrame = new RawDataFrame;
	while(fscanf(indexFile, "%ld %ld %lld %lld %f %f\n", &startOffset, &endOffset, &startFrame, &endFrame, &step1, &step2) == 6) {
		fseek(dataFile, startOffset, SEEK_SET);
		
		bool firstFrame = true;
		long long unsigned lastFrameID = 0;
		bool last1FrameLost = false;
		
		unsigned long long sumDataFrames = 0;
		unsigned long long sumDataFramesLost = 0;
		unsigned long long sumEvents = 0;
		
		while(ftell(dataFile) < endOffset) {
			fread((void *)(tmpRawDataFrame->data), sizeof(uint64_t), 2, dataFile);
			long frameSize = tmpRawDataFrame->getFrameSize();
			fread((void *)((tmpRawDataFrame->data)+2), sizeof(uint64_t), frameSize-2, dataFile);
			
			long long unsigned frameID = tmpRawDataFrame->getFrameID();
			bool frameLost = tmpRawDataFrame->getFrameLost();
			int nEvents = tmpRawDataFrame->getNEvents();

			/*
			 * Sequences of frames with zero events are suppressed after the first frame in the sequence
			 * These can be either good frames or discarded frames
			 * They are not mixed
			 */
			int framesCompacted = firstFrame ? 0 : frameID - lastFrameID - 1;
			sumDataFrames += framesCompacted;
			sumDataFramesLost += last1FrameLost ? framesCompacted : 0;

			if(!last1FrameLost) nEvents0 += framesCompacted;

			lastFrameID = frameID;
			last1FrameLost = frameLost;
			
			sumDataFrames += 1;
			sumDataFramesLost += frameLost ? 1 : 0;
			sumEvents += nEvents;

			//if(statsOnly) continue;
			//if(suppressEmpty && nEvents == 0) continue;
			
			
//			printf("%04d %016llx Size: %-4llu FrameID: %-20llu\n", 0, tmpRawDataFrame->data[0], tmpRawDataFrame->getFrameSize(), frameID);
//			printf("%04d %016llx nEvents: %20llu %4s\n", 1,  tmpRawDataFrame->data[1], tmpRawDataFrame->getNEvents(), frameLost ? "LOST" : "");

			
			if(!frameLost) {	
				if(nEvents == 0) 
					nEvents0 += 1;
				else if (nEvents < 8) 
					nEventsL += 1;
				else if (nEvents == 8)
					nEvents8 += 1;
				else
					nEventsH += 1;
			}
			
			for (int i = 0; i < nEvents; i++) {

				unsigned int channelID = tmpRawDataFrame->getEventWord(i).getChannelID();
				unsigned long tacID = tmpRawDataFrame->getEventWord(i).getTacID();
				unsigned long t1Coarse = tmpRawDataFrame->getEventWord(i).getT1Coarse();
				unsigned long t2Coarse = tmpRawDataFrame->getEventWord(i).getT2Coarse();
				unsigned long qCoarse = tmpRawDataFrame->getEventWord(i).getQCoarse();
				unsigned long t1Fine = tmpRawDataFrame->getEventWord(i).getT1Fine();
				unsigned long t2Fine = tmpRawDataFrame->getEventWord(i).getT2Fine();
				unsigned long qFine = tmpRawDataFrame->getEventWord(i).getQFine();
				
				if((channelID % 4) != 0) wrongChannelID += 1;
				if(t1Coarse != 29) wrongCoarseTime += 1; 

//				printf("%04d %016llx %016llx", 2+2*i,  tmpRawDataFrame->data[2+2*i+0], tmpRawDataFrame->data[2+2*i+1]);
//				printf(" ChannelID: (%02d %02d %02d %02d)", (channelID >> 16) % 32, (channelID >> 11) % 32, (channelID >> 5) % 64, (channelID % 32));
//				printf(" TacID: %d T1C: %4d T2C: %4d QC %4d T1F %4d T2F %4d QF %4d", tacID, t1Coarse, t2Coarse, qCoarse, t1Fine, t2Fine, qFine);
//				printf("\n");
			}
			
			
		}
		
		long long framesCompacted = endFrame - lastFrameID -1;
		sumDataFrames += framesCompacted;
		sumDataFramesLost += last1FrameLost ? framesCompacted : 0;
		nEvents0 += last1FrameLost ? 0 : framesCompacted;
		

		printf("STAT0 %llu %llu %llu\n", sumDataFrames, sumDataFramesLost, sumEvents);
		totalDataFrames += sumDataFrames;
		totalDataFramesLost += sumDataFramesLost;
	}
	printf("STAT1 %ld frames %ld frames lost \n", totalDataFrames, totalDataFramesLost);
	printf("STAT2 0: %ld L: %ld 8: %d H: %ld\n", nEvents0, nEventsL, nEvents8, nEventsH);
	printf("STAT3 BAD CH: %ld BAD TCOARSE: %ld\n", wrongChannelID, wrongCoarseTime);
	delete tmpRawDataFrame;
	
	return 0;
}
