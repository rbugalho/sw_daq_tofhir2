#include <RawReader.hpp>
#include <OverlappedEventHandler.hpp>
#include <getopt.h>
#include <assert.h>
#include <SystemConfig.hpp>
#include <CoarseSorter.hpp>
#include <ProcessHit.hpp>
#include <SimpleGrouper.hpp>

#include <boost/lexical_cast.hpp>

#include <TFile.h>
#include <TNtuple.h>
#include <TProfile.h>

using namespace PETSYS;


enum FILE_TYPE { FILE_TEXT, FILE_BINARY, FILE_ROOT };

class DataFileWriter {
private:
	double frequency;
	FILE_TYPE fileType;
	int hitLimitToWrite;
	int eventFractionToWrite;
	long long eventCounter;
        
        int refChannel;
        
        TFile* pedestalFile;
        std::map<int,std::map<int,int> > pedValues;
  
	FILE *dataFile;
	FILE *indexFile;
	off_t stepBegin;
	
	TTree *hData;
	TTree *hIndex;
	TFile *hFile;
	// ROOT Tree fields
	float		brStep1;
	float		brStep2;
        unsigned short  brPrevEventFlags;
        long long       brPrevEventTime;
        double          brTimeLast;
        double          brTimeLastTmp;
	long long 	brStepBegin;
	long long 	brStepEnd;
        
	unsigned short	brN;
        int             brChannelIdx[128];
        std::vector<double>        	brTime;
	std::vector<unsigned int>	brChannelID;
	std::vector<float>		brToT;
	std::vector<unsigned short>	brT1Coarse;
	std::vector<unsigned short>	brT1Fine;
	std::vector<unsigned short>	brT2Coarse;
	std::vector<unsigned short>	brT2Fine;
	std::vector<unsigned short>	brQCoarse;
	std::vector<unsigned short>	brQFine;
	std::vector<unsigned short>	brEnergy;
	std::vector<unsigned short>	brQT1;
	std::vector<unsigned short>	brQT2;
	std::vector<unsigned short>	brTacID;
        
        std::map<unsigned int,unsigned int> channelCount;

	struct Event {
		uint8_t mh_n; 
		uint8_t mh_j;
		long long time;
		float e;
		int id;
	} __attribute__((__packed__));
	
public:
  DataFileWriter(char *fName, double frequency, FILE_TYPE fileType, int hitLimitToWrite, int eventFractionToWrite, bool coincidence, int refChannel, TFile* pedestalFile) {
		this->frequency = frequency;
		this->fileType = fileType;
		this->hitLimitToWrite = hitLimitToWrite;
		this->eventFractionToWrite = eventFractionToWrite;
		this->eventCounter = 0;
                this->refChannel = refChannel;
                this->pedestalFile = pedestalFile;
                
                
                if( pedestalFile != NULL )
                {
                  std::cout << "pedestals!" << std::endl;
                  for(int ch = 0; ch < 128; ++ch)
                  {
                    TProfile* prof = (TProfile*)( pedestalFile->Get(Form("p_qfine_ch%d_2",ch)) );
                    if( !prof ) continue;
                    for(int jj = 0; jj < 8; ++jj)
                      (pedValues[ch])[jj] = prof->GetBinContent(jj+1);
                  }
                }
                
                
		stepBegin = 0;
                brTimeLast = -1;
                
		if (fileType == FILE_ROOT){
			hFile = new TFile(fName, "RECREATE");
			int bs = 512*1024;

			hData = new TTree("data", "Event List", 2);
			hData->Branch("step1", &brStep1, bs);
			hData->Branch("step2", &brStep2, bs);
                        hData->Branch("prevEventFlags", &brPrevEventFlags, bs);
                        hData->Branch("prevEventTime", &brPrevEventTime, bs);
                        hData->Branch("timeLast", &brTimeLast, bs);
			hData->Branch("mh_n", &brN, bs);
			hData->Branch("channelIdx", brChannelIdx, "channelIdx[128]/I");
			hData->Branch("tot", &brToT);
			hData->Branch("t1coarse", &brT1Coarse);
			hData->Branch("t1fine", &brT1Fine);
			hData->Branch("t2coarse", &brT2Coarse);
			hData->Branch("t2fine", &brT2Fine);
			hData->Branch("qcoarse", &brQCoarse);
			hData->Branch("qfine", &brQFine);
			hData->Branch("time", &brTime);
			hData->Branch("channelID", &brChannelID);
			hData->Branch("energy", &brEnergy);
			hData->Branch("qT1", &brQT1);
			hData->Branch("qT2", &brQT2);
			hData->Branch("tacID", &brTacID);
			
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
			dataFile = fopen(fName, "w"); // 
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
			hFile->Write();
		}
		else if(fileType == FILE_BINARY) {
			fprintf(indexFile, "%llu\t%llu\t%e\t%e\n", stepBegin, ftell(dataFile), step1, step2);
			stepBegin = ftell(dataFile);
		}
		else {
                  // Do nothing
		}
	};
	
  void addEvents(float step1, float step2,EventBuffer<GammaPhoton> *buffer, bool coincidence, int refChannel, bool pedestals) {
		bool writeMultipleHits = false;
                
		double Tps = 1E12/frequency;
		float Tns = Tps / 1000;
                
		long long tMin = buffer->getTMin() * (long long)Tps;
                
                
                // std::cout << "frequency: " << frequency << "   Tps: " << Tps << "   Tns: " << Tns << "   tMin: " << tMin << " (ps)" << std::endl;
		int N = buffer->getSize();
		for (int i = 0; i < N; i++) {
			long long tmpCounter = eventCounter;
			eventCounter += 1;
			if((tmpCounter % 1024) >= eventFractionToWrite) continue;

			GammaPhoton &p = buffer->get(i);
			
			brTime.clear();
			brChannelID.clear();
			brToT.clear();
			brT1Coarse.clear();
			brT1Fine.clear();
			brT2Coarse.clear();
			brT2Fine.clear();
			brQCoarse.clear();
			brQFine.clear();
			brEnergy.clear();
			brQT1.clear();
			brQT2.clear();
			brTacID.clear();
			for(unsigned int jj = 0; jj < 128; ++jj) brChannelIdx[jj] = -1;
			channelCount.clear();
			
                        brTimeLast = brTimeLastTmp;
                        brTimeLastTmp = 0; 
                        
			if(!p.valid) continue;
			brN  = p.nHits;
			int limit = (hitLimitToWrite < p.nHits) ? hitLimitToWrite : p.nHits;
			if( coincidence && limit < 2 ) continue;
                        bool hasRefChannel = false;
			for(int m = 0; m < limit; m++) {
				Hit &h = *p.hits[m];
				float Eunit = 1.0;
				unsigned int chID = h.raw->channelID;
				
                                if( chID == refChannel ) hasRefChannel = true;
                                
				if (fileType == FILE_ROOT){
					brStep1 = step1;
					brStep2 = step2;
					
					if( channelCount[chID] == 0 )
                                        {
                                          channelCount[chID] += 1;
					  brChannelIdx[chID] = brTime.size();
                                          
                                          brPrevEventTime = ((long long)((h.raw->time - h.raw->prevEventTime) * Tps));
                                          brPrevEventFlags = h.raw->prevEventFlags;
                                          
                                          if( brTimeLastTmp == 0 || (((long long)(h.time * Tps)) + tMin) < brTimeLastTmp )
                                            brTimeLastTmp = ((long long)(h.time * Tps)) + tMin;
                                          
                                          brTime.emplace_back( ((long long)(h.time * Tps)) + tMin );
                                          brChannelID.emplace_back( chID );
                                          brToT.emplace_back( (h.timeEnd - h.time) * Tps );
					  brT1Coarse.emplace_back( long(h.time) & 0x3FF );
					  brT1Fine.emplace_back( h.raw->t1fine );
					  brT2Coarse.emplace_back( long(h.timeEnd) & 0x3FF );
					  brT2Fine.emplace_back( h.raw->t2fine );
                                          brQCoarse.emplace_back( long(h.timeEnd) & 0x3FF );
                                          brQFine.emplace_back( h.raw->qfine );
                                          if( !pedestals ) brEnergy.emplace_back( h.energy * Eunit );
                                          else brEnergy.emplace_back( h.raw->qfine - (pedValues[chID])[h.raw->tacID] );
					  brQT1.emplace_back( h.qT1 );
					  brQT2.emplace_back( h.qT2 );
                                          brTacID.emplace_back( h.raw->tacID );
                                        }
                                        else
                                        {
                                          channelCount[chID] += 1;                                        
                                        }
				}
				else if(fileType == FILE_BINARY) {
					Event eo = { 
						(uint8_t)p.nHits, (uint8_t)m,
						((long long)(h.time * Tps)) + tMin,
						h.energy * Eunit,
						(int)h.raw->channelID
					};
					fwrite(&eo, sizeof(eo), 1, dataFile);
				}
				else {
					fprintf(dataFile, "%d\t%d\t%lld\t%f\t%d\n",
						p.nHits, m,
						((long long)(h.time * Tps)) + tMin,
						h.energy * Eunit,
						h.raw->channelID
					);
				}
			}
                        
			if( !coincidence || (coincidence && limit > 1 && ( hasRefChannel || refChannel == -1) ) )
			  hData->Fill();
		}
		
	};
	
};

class WriteHelper : public OverlappedEventHandler<GammaPhoton, GammaPhoton> {
private: 
	DataFileWriter *dataFileWriter;
	float step1;
	float step2;
        bool coincidence;
        int refChannel;
        bool pedestals;
public:
         WriteHelper(DataFileWriter *dataFileWriter, float step1, float step2, bool coincidence, int refChannel, bool pedestals, EventSink<GammaPhoton> *sink) :
		OverlappedEventHandler<GammaPhoton, GammaPhoton>(sink, true),
		dataFileWriter(dataFileWriter), step1(step1), step2(step2), coincidence(coincidence), refChannel(refChannel), pedestals(pedestals)
	{
	};
	
	EventBuffer<GammaPhoton> * handleEvents(EventBuffer<GammaPhoton> *buffer) {
          dataFileWriter->addEvents(step1, step2, buffer, coincidence, refChannel, pedestals);
		return buffer;
	};
};

void displayHelp(char * program)
{
	fprintf(stderr, "Usage: %s --config <config_file> -i <input_file_prefix> -o <output_file_prefix> [optional arguments]\n", program);
	fprintf(stderr, "Arguments:\n");
	fprintf(stderr,  "  --config \t\t Configuration file containing path to tdc calibration table \n");
	fprintf(stderr,  "  -i \t\t\t Input file prefix - raw data\n");
	fprintf(stderr,  "  -o \t\t\t Output file name - by default in text data format\n");
	fprintf(stderr, "Optional flags:\n");
	fprintf(stderr,  "  --writeBinary \t Set the output data format to binary\n");
	fprintf(stderr,  "  --writeRoot \t\t Set the output data format to ROOT TTree\n");
	fprintf(stderr,  "  --writeMultipleHits N \t\t Writes multiple hits, up to the Nth hit\n");
	fprintf(stderr,  "  --writeFraction N \t\t Fraction of events to write. Default: 100%.\n");
        fprintf(stderr,  "  --coincidence \t Only save coincidences\n");
        fprintf(stderr,  "  --refChannel \t Reference channel\n");
        fprintf(stderr,  "  --pedestals \t Use pedestals in energy reconstruction\n");
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
	int hitLimitToWrite = 128;
	long long eventFractionToWrite = 1024;
        bool coincidence = false;
        int refChannel = -1;
        bool pedestals;

        static struct option longOptions[] = {
                { "help", no_argument, 0, 0 },
                { "config", required_argument, 0, 0 },
		{ "writeBinary", no_argument, 0, 0 },
		{ "writeRoot", no_argument, 0, 0 },
		{ "writeMultipleHits", required_argument, 0, 0},
		{ "writeFraction", required_argument },
		{ "coincidence", no_argument, 0, 0 },
		{ "refChannel", required_argument, 0, 0 },
		{ "pedestals", no_argument, 0, 0 }
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
			case 4:		hitLimitToWrite = boost::lexical_cast<int>(optarg); break;
			case 5:		eventFractionToWrite = round(1024 *boost::lexical_cast<float>(optarg) / 100.0); break;
                        case 6:         coincidence = true; break;
                        case 7:         refChannel = boost::lexical_cast<int>(optarg); break;
                        case 8:         pedestals = true; break;
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
        
        TFile* pedestalFile = NULL;
        if(pedestals){
          std::string pedestalFileName(Form("%s_pedestals.root",inputFilePrefix));
          size_t pos = pedestalFileName.find("raw");
          pedestalFileName.replace(pos,3,"reco");
          pedestalFile = TFile::Open(pedestalFileName.c_str(),"READ");
        }
        
	RawReader *reader = RawReader::openFile(inputFilePrefix);
	
	// If data was taken in ToT mode, do not attempt to load these files
	unsigned long long mask = SystemConfig::LOAD_ALL;
	if(reader->isTOT()) {
		mask ^= (SystemConfig::LOAD_QDC_CALIBRATION | SystemConfig::LOAD_ENERGY_CALIBRATION);
	}
	SystemConfig *config = SystemConfig::fromFile(configFileName, mask);
	
	DataFileWriter *dataFileWriter = new DataFileWriter(outputFileName, reader->getFrequency(), fileType, hitLimitToWrite, eventFractionToWrite, coincidence, refChannel, pedestalFile);
	
	for(int stepIndex = 0; stepIndex < reader->getNSteps(); stepIndex++) {
		float step1, step2;
		reader->getStepValue(stepIndex, step1, step2);
		printf("Processing step %d of %d: (%f, %f)\n", stepIndex+1, reader->getNSteps(), step1, step2);
		fflush(stdout);
		reader->processStep(stepIndex, true,
				new CoarseSorter(
				new ProcessHit(config, reader,
				new SimpleGrouper(config,
                                new WriteHelper(dataFileWriter, step1, step2, coincidence, refChannel, pedestals,
				new NullSink<GammaPhoton>()
				)))));
		
		dataFileWriter->closeStep(step1, step2);
	}

	delete dataFileWriter;
	delete reader;

	return 0;
}
