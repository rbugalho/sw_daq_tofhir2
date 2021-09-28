#ifndef __PETSYS__ABSTRACTRAW_READER_HPP__DEFINED__
#define __PETSYS__ABSTRACTRAW_READER_HPP__DEFINED__

#include <EventSourceSink.hpp>
#include <Event.hpp>

#include <vector>

namespace PETSYS {
	class AbstractRawReader {
	public:
		virtual ~AbstractRawReader() {};
		virtual bool isQDC() = 0;
		virtual double getFrequency() = 0;
		virtual int getNSteps() = 0;
		virtual void getStepValue(int n, float &step1, float &step2) = 0;
		virtual void processStep(int n, bool verbose, EventSink<RawHit> *pipeline) = 0;
		virtual void readThrValues(char* inputFilePrefix, float& step1, float& step2) {};
	};
}

#endif // __PETSYS__ABSTRACTRAW_READER_HPP__DEFINED__
