#ifndef __PETSYS_EVENT_HPP__DEFINED__
#define __PETSYS_EVENT_HPP__DEFINED__

#include <cstddef>
#include <sys/types.h>
#include <stdint.h>

namespace PETSYS {

	struct RawHit {
		bool valid;
		long long time;
		long long timeEnd;
		long long timeEndQ;
		unsigned short prevEventFlags;
		long prevEventTime;
		unsigned int channelID;

		unsigned short t1fine;
		unsigned short t2fine;
		unsigned short qfine;
		unsigned short tacID;

		RawHit() {
			valid = false;
		};
	};

	struct Hit {
		bool valid;
		RawHit *raw;
		double time;
		double timeEnd;
		float energy;
		
		float qT1;
		float qT2;
		
		short bar;
		short tb;
		short region;
		
		Hit() {
			valid = false;
			raw = NULL;
		};
	};
	
	struct BarHit {
		bool valid;
		double time;
	
		short bar;
		short region;
		Hit *top;
		Hit *bottom;
		
		BarHit() {
			valid = false;
			top = NULL;
			bottom = NULL;
		};
	};

	struct GammaPhoton {
		static const int maxHits = 256;
		bool valid;
		double time;
		short region;
		int nHits;
		BarHit *hits[maxHits];

		GammaPhoton() {
			valid = false;
			for(int i = 0; i < maxHits; i++)
				hits[i] = NULL;
		};
	};

	struct Coincidence {
		static const int maxPhotons = 2;
		bool valid;
		double time;
		int nPhotons;
		GammaPhoton *photons[maxPhotons];
		
		Coincidence() {
			valid = false;
			for(int i = 0; i < maxPhotons; i++)
				photons[i] = NULL;
		};
	};
	
	class EventStream {
	public:
		//virtual bool isQDC(unsigned int gChannelID) = 0;
		virtual double getFrequency() = 0;
		virtual int getTriggerID() = 0;

		
	};
}
#endif
