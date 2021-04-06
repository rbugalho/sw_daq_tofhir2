#ifndef __PETSYS__SHM_RAW_HPP__DEFINED__
#define __PETSYS__SHM_RAW_HPP__DEFINED__

#include <stdint.h>
#include <string>
#include <event_decode.hpp>
#include <sys/mman.h>

namespace PETSYS {
	
static const int MaxRawDataFrameSize = 2048;
static const unsigned MaxRawDataFrameQueueSize = 16*1024;


struct RawDataFrame {
	uint64_t data[MaxRawDataFrameSize];

	unsigned getFrameSize() {
		uint64_t eventWord = data[0];
		return (eventWord >> 36) & 0x7FFF;
	};
	

	unsigned long long getFrameID() {
		uint64_t eventWord = data[0];
		return eventWord & 0xFFFFFFFFFULL;
	};

	bool getFrameLost() {
		uint64_t eventWord = data[1];
		return (eventWord & 0x18000) != 0;
	};

	int getNEvents() {
		uint64_t eventWord = data[1];
		return (eventWord & 0x7FFF)/2;
	}; 
	
	RawEventWord getEventWord(int event)
	{
		uint64_t word_h = data[2 + 2*event + 0];
		uint64_t word_l = data[2 + 2*event + 1];
		
		unsigned __int128 word = 0x0;
		word = (word_h >> 54);  // Port ID, slave ID
		word = (word << 44) | (word_h & 0xfffffffffff); // Event top half
		word = (word << 44) | (word_l & 0xfffffffffff); // Event bottom
		
		return RawEventWord(word);
	};
	
};

class SHM_RAW {
public:
	SHM_RAW(std::string path);
	~SHM_RAW();

	unsigned long long getSizeInBytes();
	unsigned long long  getSizeInFrames() { 
		return MaxRawDataFrameQueueSize;
	};
	
	RawDataFrame *getRawDataFrame(int index) {
		RawDataFrame *dataFrame = &shm[index];
		return dataFrame;
	}

	
	unsigned getFrameSize(int index) {
		return  getRawDataFrame(index)->getFrameSize();
	};
	

	unsigned long long getFrameID(int index) {
		return  getRawDataFrame(index)->getFrameID();
	};

	bool getFrameLost(int index) {
		return  getRawDataFrame(index)->getFrameLost();
	};

	int getNEvents(int index) {
		return  getRawDataFrame(index)->getNEvents();
	}; 
	
	RawEventWord getRawEventWord(int index, int event)  { return getRawDataFrame(index)->getEventWord(event); };
	unsigned short getQFine(int index, int event)       { return getRawDataFrame(index)->getEventWord(event).getQFine(); };
	unsigned short getQCoarse(int index, int event)     { return getRawDataFrame(index)->getEventWord(event).getQCoarse(); };
	unsigned short getT2Fine(int index, int event)      { return getRawDataFrame(index)->getEventWord(event).getT2Fine(); };
	unsigned short getT2Coarse(int index, int event)    { return getRawDataFrame(index)->getEventWord(event).getT2Coarse(); };
	unsigned short getT1Fine(int index, int event)      { return getRawDataFrame(index)->getEventWord(event).getT1Fine(); };
	unsigned short getT1Coarse(int index, int event)    { return getRawDataFrame(index)->getEventWord(event).getT1Coarse(); };
	unsigned short getPrevEventTime(int index, int event)    { return getRawDataFrame(index)->getEventWord(event).getPrevEventTime(); };
	unsigned short getPrevEventFlags(int index, int event) { return getRawDataFrame(index)->getEventWord(event).getPrevEventFlags(); };
	unsigned short getTacID(int index, int event)       { return getRawDataFrame(index)->getEventWord(event).getTacID(); };
	unsigned int getChannelID(int index, int event)   { return getRawDataFrame(index)->getEventWord(event).getChannelID(); };


private:
	int shmfd;
	RawDataFrame *shm;
	off_t shmSize;
};

}
#endif


