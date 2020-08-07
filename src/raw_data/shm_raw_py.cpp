#include <boost/python.hpp>
using namespace boost::python;

#include "shm_raw.hpp"
using namespace PETSYS;

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
	;
}
