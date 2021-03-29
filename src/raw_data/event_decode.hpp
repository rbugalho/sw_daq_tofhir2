#ifndef __PETSYS__EVENT_DECODE_HPP__DEFINED__
#define __PETSYS__EVENT_DECODE_HPP__DEFINED__

#include <stdint.h>
#include <string>
#include <stdio.h>

namespace PETSYS {       

class RawEventWord{

public:
	RawEventWord() : word(0) {};
	RawEventWord(unsigned __int128 word) : word(word){};
	~RawEventWord() {};
	
	bool operator<(const RawEventWord &b) const { return this->word < b.word; };
	
	
	unsigned short getT1Coarse()	{ return (word >> 73) % 1024; };
	unsigned short getT2Coarse()	{ return (word >> 63) % 1024; };
	unsigned short getQCoarse()	{ return (word >> 53) % 1024; };
	unsigned short getQFine()	{ return (word >> 43) % 1024; };
	unsigned short getT2Fine()	{ return (word >> 33) % 1024; };
	unsigned short getT1Fine()	{ return (word >> 23) % 1024; };
	unsigned short getPrevEventTime()	{ return (word >> 13) % 1024; };
	unsigned short getPrevEventFlags()	{ return (word >> 8) % 16; };
	unsigned short getTacID()	{ return (word >> 5) % 8; };
	unsigned int getChannelID()   { 
		unsigned __int128 asicID = (word >> 83) % 8;
		unsigned __int128 channelID = (word % 32);
		unsigned int r = (asicID << 5) | channelID;
		return r;
	};
	
public:
	unsigned __int128 word;

};

}
#endif
