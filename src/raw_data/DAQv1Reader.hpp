#ifndef __PETSYS__DAQV1_READER_HPP__DEFINED__
#define __PETSYS__DAQV1_READER_HPP__DEFINED__

#include <EventSourceSink.hpp>
#include <AbstractRawReader.hpp>

#include <Event.hpp>

#include <vector>

namespace PETSYS {
	class DAQv1Reader : public AbstractRawReader {
	public:
		~DAQv1Reader();
		static DAQv1Reader *openFile(const char *fnPrefix, FILE *decoder_log = NULL);

		bool isQDC();
		double getFrequency();
		int getNSteps();
		void getStepValue(int n, float &step1, float &step2);
		void processStep(int n, bool verbose, EventSink<RawHit> *pipeline);
		void readThrValues(char* inputFilePrefix, float& step1, float& step2);
		void processLastStep(bool verbose, EventSink<RawHit> *pipeline);

	private:
		DAQv1Reader();
		void processRange(unsigned long begin, unsigned long end, bool verbose, EventSink<RawHit> *pipeline);

		FILE * dataFile;
		FILE * decoder_log;

		
	};
}

#endif // __PETSYS__DAQV1_READER_HPP__DEFINED__
