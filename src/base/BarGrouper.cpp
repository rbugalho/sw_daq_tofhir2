#include "BarGrouper.hpp"
#include <vector>
#include <math.h>

using namespace PETSYS;
using namespace std;

BarGrouper::BarGrouper(SystemConfig *systemConfig, EventSink<BarHit> *sink) :
	systemConfig(systemConfig), OverlappedEventHandler<Hit, BarHit>(sink, false)
{
	nHitsReceived = 0;
	nHitsReceivedValid = 0;
	nBarHits = 0;
	nBarHitsDouble = 0;
	nBarHitsTop = 0;
	nBarHitsBottom = 0;
	nBarHitsOther = 0;
}

BarGrouper::~BarGrouper()
{
}

void BarGrouper::report()
{
	fprintf(stderr, ">> BarGrouper report\n");
	fprintf(stderr, " hits received\n");
	fprintf(stderr, "  %10u total\n", nHitsReceived);
	fprintf(stderr, "  %10u (%4.1f%%) invalid\n", nHitsReceived - nHitsReceivedValid, 100.0 * (nHitsReceived - nHitsReceivedValid)/nHitsReceived);
	fprintf(stderr, " bar hits found\n");
	fprintf(stderr, "  %10u total\n", nBarHits);
	fprintf(stderr, "  %10u (%4.1f%%) dual readout hits\n", nBarHitsDouble, 100.0 * nBarHitsDouble / nBarHits);
	fprintf(stderr, "  %10u (%4.1f%%) top only hits\n", nBarHitsTop, 100.0 * nBarHitsTop / nBarHits);
	fprintf(stderr, "  %10u (%4.1f%%) bottom only hits\n", nBarHitsBottom, 100.0 * nBarHitsBottom / nBarHits);
	fprintf(stderr, "  %10u (%4.1f%%) other hits\n", nBarHitsOther, 100.0 * nBarHitsOther / nBarHits);

	OverlappedEventHandler<Hit, BarHit>::report();
}

EventBuffer<BarHit> * BarGrouper::handleEvents(EventBuffer<Hit> *inBuffer)
{
	uint32_t lHitsReceived = 0;
	uint32_t lHitsReceivedValid = 0;
	uint32_t lBarHits = 0;
	uint32_t lBarHitsDouble = 0;
	uint32_t lBarHitsTop = 0;
	uint32_t lBarHitsBottom = 0;
	uint32_t lBarHitsOther = 0;
	
	
	
	double timeWindow1 = systemConfig->sw_trigger_bar_time_window;

	unsigned N =  inBuffer->getSize();
	EventBuffer<BarHit> * outBuffer = new EventBuffer<BarHit>(N, inBuffer);
	vector<bool> taken(N, false);
	
	for(unsigned i = 0; i < N; i++) {
		// Do accounting first
		Hit &hit = inBuffer->get(i);
		lHitsReceived += 1;

		if(!hit.valid) continue;
		lHitsReceivedValid += 1;

		if (taken[i]) continue;
		taken[i] = true;
		
		Hit *otherHit = NULL;
		for(int j = i+1; j < N; j++) {
			// Special case, these hits should not be top/bottom matched
			if(hit.tb == -1) break;
			
			
			Hit &hit2 = inBuffer->get(j);
			if(!hit2.valid) continue;
			if(taken[j]) continue;
			
			// Stop searching for more hits for this photon
			if((hit2.time - hit.time) > (overlap + timeWindow1)) break;
			
			// if(!systemConfig->isMultiHitAllowed(hit2.region, hit.region)) continue;
			if(fabs(hit.time - hit2.time) > timeWindow1) continue;
			if(hit.bar != hit2.bar) continue;
			if(hit.tb == hit2.tb) continue;
			
			taken[j] = true;
			otherHit = &hit2;
			break;
			
		}
		
		BarHit &barHit = outBuffer->getWriteSlot();
		if(hit.tb == 1) {
			barHit.top = &hit;
			barHit.bottom = otherHit;
		}
		else {
			barHit.bottom = &hit;
			barHit.top = otherHit;
		}
		
		barHit.bar = hit.bar;
		
		if((otherHit == NULL) || (hit.time < otherHit->time)) {
			barHit.time = hit.time;
		}
		else {
			barHit.time = otherHit->time;
		}
		
		
		barHit.valid = true;
		outBuffer->pushWriteSlot();
		
		lBarHits += 1;
		
		
		if(otherHit != NULL)
			lBarHitsDouble += 1;
		else if (hit.tb == 1) 
			lBarHitsTop += 1;
		else if(hit.tb == 0)
			lBarHitsBottom += 1;
		else
			lBarHitsOther += 1;
		
	}
	
	
	atomicAdd(nHitsReceived, lHitsReceived);
	atomicAdd(nHitsReceivedValid, lHitsReceivedValid);
	atomicAdd(nBarHits, lBarHits);
	atomicAdd(nBarHitsDouble, lBarHitsDouble);
	atomicAdd(nBarHitsTop, lBarHitsTop);
	atomicAdd(nBarHitsBottom, lBarHitsBottom);
	atomicAdd(nBarHitsOther, lBarHitsOther);
	
	return outBuffer;
}

