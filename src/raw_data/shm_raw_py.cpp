#include <stdio.h>

#include <boost/python.hpp>
using namespace boost::python;

#include "shm_raw.hpp"
using namespace PETSYS;


struct unpacked_event_t {
	unsigned long long frameID;
	unsigned int channelID;
	unsigned short tacID;
	unsigned short t1Coarse;
	unsigned short t2Coarse;
	unsigned short qCoarse;
	unsigned short t1Fine;
	unsigned short t2Fine;
	unsigned short qFine;
};


static object events_as_bytes(SHM_RAW &self, int start, int end)
{
	auto shm_raw_size = self.getSizeInFrames();
	int total_events = 0;
	for(auto ii = start; ii < end; ii++) {
		auto index = ii % shm_raw_size;
		total_events += self.getNEvents(index);
	}

	auto buffer_size = total_events * sizeof(unpacked_event_t);
	unpacked_event_t * buf = (unpacked_event_t *)malloc(buffer_size);
	unpacked_event_t *p = buf;
	for(auto ii = start; ii < end; ii++) {
		auto index = ii % shm_raw_size;

		unsigned long long frameID = self.getFrameID(index);
		auto n_events = self.getNEvents(index);
		for(auto j = 0; j < n_events; j++) {
			p->frameID = frameID;
			p->channelID = self.getChannelID(index, j);
			p->tacID = self.getTacID(index, j);
			p->t1Coarse = self.getT1Coarse(index, j);
			p->t2Coarse = self.getT2Coarse(index, j);
			p->qCoarse = self.getQCoarse(index, j);
			p->t1Fine = self.getT1Fine(index, j);
			p->t2Fine = self.getT2Fine(index, j);
			p->qFine = self.getQFine(index, j);
			p++;
		}
	}

	PyObject* py_buf = PyBytes_FromStringAndSize((char *)buf, buffer_size);
	object retval = object(handle<>(py_buf));
	return retval;
}

BOOST_PYTHON_MODULE(shm_raw)
{


	class_<SHM_RAW>("SHM_RAW", init<std::string>())
		.def("getSizeInBytes", &SHM_RAW::getSizeInBytes)
		.def("getSizeInFrames", &SHM_RAW::getSizeInFrames)
		.def("getFrameSize", &SHM_RAW::getFrameSize)
		.def("getFrameID", &SHM_RAW::getFrameID)
		.def("getFrameLost", &SHM_RAW::getFrameLost)
		.def("getNEvents", &SHM_RAW::getNEvents)
		.def("getT1Coarse", &SHM_RAW::getT1Coarse)
		.def("getT1Fine", &SHM_RAW::getT1Fine)
		.def("getT2Coarse", &SHM_RAW::getT2Coarse)
		.def("getT2Fine", &SHM_RAW::getT2Fine)
		.def("getQCoarse", &SHM_RAW::getQCoarse)
		.def("getQFine", &SHM_RAW::getQFine)
		.def("getTacID", &SHM_RAW::getTacID)
		.def("getChannelID", &SHM_RAW::getChannelID)
		.def("events_as_bytes", &events_as_bytes, (arg("self"), arg("start"), arg("end")))
	;
}
