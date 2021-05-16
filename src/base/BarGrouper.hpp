#ifndef __PETSYS_BAR_GROUPER_HPP__DEFINED__
#define __PETSYS_BAR_GROUPER_HPP__DEFINED__

#include <SystemConfig.hpp>
#include <OverlappedEventHandler.hpp>
#include <Event.hpp>
#include <Instrumentation.hpp>

namespace PETSYS {
	
class BarGrouper : public OverlappedEventHandler<Hit, BarHit> {
public:
	BarGrouper(SystemConfig *systemConfig, EventSink<BarHit> *sink);
	~BarGrouper();
	
	virtual void report();
	
protected:
	virtual EventBuffer<BarHit> * handleEvents(EventBuffer<Hit> *inBuffer);
		
private:
	SystemConfig *systemConfig;

	uint32_t nHitsReceived;
	uint32_t nHitsReceivedValid;
	uint32_t nBarHits;
	uint32_t nBarHitsDouble;
	uint32_t nBarHitsTop;
	uint32_t nBarHitsBottom;
	uint32_t nBarHitsOther;
};

}
#endif // __PETSYS_BAR_GROUPER_HPP__DEFINED__