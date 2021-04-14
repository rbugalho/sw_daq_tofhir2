# -*- coding: utf-8 -*-
from bitarray import bitarray
from bitarray_utils import intToBin, binToInt, grayToBin, grayToInt
import sys


def bit_range(msb, lsb):
	if msb > lsb:
		return [ n for n in range(msb, lsb-1, -1) ]
	elif msb == lsb:
		return  [ msb ]
	else:
		return [ n for n in range(lsb, msb+1, 1) ]


def compile_cfg_map(*args):
	total_length = 0
	bits_used = set()
	result_map = []
	for n in range(0, len(args), 2):
		for name, msb, lsb, default in args[n+1]:
			name = name.lower()
			bits = bit_range(total_length + msb, total_length + lsb)

			intersection = bits_used.intersection(set(bits))
			if intersection != set():
				sys.stderr.write("ERROR in field %s: bits %s already used\n"  % (name, (", ").join([b for b in intersection])))
				sys.exit(1)

			bits_used = bits_used.union(set(bits))
			result_map.append((name, bits, default))

		total_length += args[n]
	
	return total_length, result_map



## Contains parameters and methods related to the global operation of one ASIC. 
class AbstractConfig(bitarray):
	## Constructor. 
	# Defines and sets all fields to default values. Most important fields are:
	# 
	def __init__(self,  endian="big"):
		super(AbstractConfig, self).__init__()


		return None

	def __deepcopy__(self, memo):
		return AsicGlobalConfig(initial=self)
		

	## Set the value of a given parameter as an integer
	# @param key  String with the name of the parameter to be set
	# @param value  Integer corresponding to the value to be set	
	def setValue(self, key, value):
		key = key.lower()
		b = intToBin(value, len(self.fields[key]))
		self.setBits(key, b)

	## Set the value of a given parameter as a bitarray
	# @param key  String with the name of the parameter to be set
	# @param value  Bitarray corresponding to the value to be set		
	def setBits(self, key, value):
		key = key.lower()
		index = self.fields[key]
		assert len(value) == len(index)
		for a,b in enumerate(index):
			self[self.l - 1 - b] = value[a]

	## Returns the value of a given parameter as a bitarray
	# @param key  String with the name of the parameter to be returned	
	def getBits(self, key):
		key = key.lower()
		index = self.fields[key]
		value = bitarray(len(index))
		for a,b in enumerate(index):
			value[a] = self[self.l - 1 - b]
		return value

	## Returns the value of a given parameter as an integer
	# @param key  String with the name of the parameter to be returned	
	def getValue(self, key):
		key = key.lower()
		return binToInt(self.getBits(key))

	## Prints the content of all parameters as a bitarray	
	def printAllBits(self):
		for key in self.fields.keys():
			print key, " : ", self.getBits(key)

	## Prints the content of all parameters as integers
	def printAllValues(self):
		unsorted = [ (min(bitList), name) for name, bitList in self.fields.items() ]
		unsorted.sort()
		for b, key in unsorted:
			bitList = self.fields[key]
			l = bitList[0]
			r = bitList[-1]
			#print "%30s : %3d : %20s : %d..%d" % (key, self.getValue(key), self.getBits(key), l, r)
			c_decimal = "%d'd%d" % (len(bitList), self.getValue(key))
			c_binary = format(self.getValue(key), "0%db" % len(bitList))
			c_binary = "%d'b%s" % (len(bitList), c_binary)
			print "// [%03d:%03d] %-30s (default %6s | %10s )" % (l, r, key, c_decimal, c_binary)

	## Returns all the keys (variables) in this class
	def getKeys(self):
		return self.fields.keys()
	
class AsicGlobalConfig(AbstractConfig):
	## Constructor. 
	# Defines and sets all fields to default values. Most important fields are:
	# 
	def __init__(self, initial=None, endian="big"):
		super(AsicGlobalConfig, self).__init__()

		fields_d3 = [
			("c_r_clk_en", 5, 0,		3),
			("c_tac_refresh_en", 6, 6,	1),
			("c_tac_refresh_t", 18, 7,	3),
			("c_counter_en", 19, 19,	0),
			("c_counter_t", 43, 20,		0),
			("c_l0_enable", 45, 44,		0b11),
			("c_l0_latency", 57, 46,	0),
			("c_l1_enable", 59, 58,		0),
			("c_l1_latency", 71, 60,	0),
			("c_tp_en", 72, 72,		0),
			("c_tp_inv", 73, 73,		0),
			("c_tp_period", 83, 74,		0),
			("c_tp_length", 93, 84,		0),
			("c_counter_lost", 94, 94,	0),
			("c_aldo_en", 96, 95,		0),
			("c_aldo_range", 98, 97,	0)
		]
		l_d3 = 99

		fields_d2 = [
			("c_ext_tp_en", 0, 0, 0),
			("c_fetp_en", 1, 1, 0),
			("c_veto_en", 2, 2, 0),
			("c_int_tp_delay", 5, 3, 0)
		]
		l_d2 = 6


		fields_mb = [
			("Enable_postamp_T_mirrors", 0, 0, 1),
			("Postamp_T_bias_DAC", 6, 1, 32),
			("Enable_preamp_mirrors", 7, 7, 1),
			("Preamp_bias_DAC", 13, 8, 32),
			("Enable_postamp_E_mirrors", 14, 14, 1),
			("Postamp_E_bias_DAC", 20, 15, 32),
			("Enable_attenuator_mirrors", 21, 21, 1),
			("Attenuator_bias_DAC", 27, 22, 32),
			("Enable_TAC1_mirrors", 28, 28, 1),
			("TAC1_bias_DAC", 34, 29, 32),
			("Enable_discriminator_mirrors", 35, 35, 1),
			("Discriminator_bias_DAC", 41, 36, 32),
			("Enable_TAC2_mirrors", 42, 42, 1),
			("TAC2_bias_DAC", 48, 43, 32),
			("Enable_QAC_mirrors", 49, 49, 1),
			("QAC_bias_DAC", 55, 50, 32),
			("Enable_ADC_mirrors", 56, 56, 1),
			("ADC_bias_DAC", 62, 59, 32),
			("EFUSE_A", 65, 63, 0),
			("MUX_SEL", 68, 66, 0),
			("MUX_EN", 69, 69, 0),
			("Pulse_Amplitude", 74, 70, 0),
			("Comparator_enable", 75, 75, 0),
			("Iref_probe_enable", 76, 76, 0),
			("Iref_cal_DAC", 84, 77, 177),
			("Valdo_A_Gain", 85, 85, 0),
			("Valdo_A_DAC", 93, 86, 0),
			("Valdo_B_Gain", 94, 94, 0),
			("Valdo_B_DAC", 102, 95, 0),
			("Amp_Vbl_DAC", 108, 103, 32),
			("TAC_QAC_Vbl_DAC", 114, 109, 54),
			("SE2Diff_CM_DAC", 120, 115, 32)
		]
		l_mb = 121

		l, f = compile_cfg_map (
			l_d3, fields_d3,
			l_d2, fields_d2,
			l_mb, fields_mb
		)

		self.l = l
		self.fields = {}
		for name, bits, default in f:
			self.fields[name] = bits

		if initial is not None:
			# We have an initial value, let's just go with it!
			self[0:self.l] = bitarray(initial)
			return None


		self[0:self.l] = bitarray(self.l)
		self.setall(False)
		for name, bits, default in f:
			self.setValue(name, default)


		return None

	def __deepcopy__(self, memo):
		return AsicGlobalConfig(initial=self)
		

		return self.fields.keys()
	
class AsicGlobalConfigTX(AbstractConfig):
	## Constructor. 
	# Defines and sets all fields to default values. Most important fields are:
	# 
	def __init__(self, initial=None, endian="big"):
		super(AsicGlobalConfigTX, self).__init__()

		fields_d3 = [
			("c_tx_mode",	3,	0,	0),
			("c_tx_clps",	13,	4,	0x3FF)
		]
		l_d3 = 14


		l, f = compile_cfg_map (l_d3, fields_d3)

		self.l = l
		self.fields = {}
		for name, bits, default in f:
			self.fields[name] = bits

		if initial is not None:
			# We have an initial value, let's just go with it!
			self[0:self.l] = bitarray(initial)
			return None


		self[0:self.l] = bitarray(self.l)
		for name, bits, default in f:
			self.setValue(name, default)


		return None

	def __deepcopy__(self, memo):
		return AsicGlobalConfigTX(initial=self)
		

		return self.fields.keys()	


class AsicGlobalConfigStatus(AbstractConfig):
	## Constructor. 
	# Defines and sets all fields to default values. Most important fields are:
	# 
	def __init__(self, initial=None, endian="big"):
		super(AsicGlobalConfigStatus, self).__init__()

		fields_d3 = [
			("status_drx_recv",		1,	0, 	0),
			("status_resync_recv",		3,	2, 	0),
			("status_trigger_recv",		5,	4, 	0),
			("status_seu_count",		37,	6, 	0),
			("status_calibration_comparator",38,	38, 	0),
			("cfg_chip_id",			43,	39, 	0)
		]
		l_d3 = 44


		l, f = compile_cfg_map (l_d3, fields_d3)

		self.l = l
		self.fields = {}
		for name, bits, default in f:
			self.fields[name] = bits

		if initial is not None:
			# We have an initial value, let's just go with it!
			self[0:self.l] = bitarray(initial)
			return None


		self[0:self.l] = bitarray(self.l)
		for name, bits, default in f:
			self.setValue(name, default)


		return None

	def __deepcopy__(self, memo):
		return AsicGlobalConfigStatus(initial=self)
		

		return self.fields.keys()	

## Contains parameters and methods related to the operation of one channel of the ASIC. 
class AsicChannelConfig(AbstractConfig):
	## Constructor
	# Defines and sets all fields to default values. Most important fields are:
	# 
	def __init__(self, initial=None, endian="big"):
		super(AsicChannelConfig, self).__init__()

		fields_d3 = [
			("c_latch_B",		0,	0, 	0),
			("c_max_v_en",		1,	1,	1),
			("c_max_v",		10,	2,	0),
			("c_min_q",		19,	11,	0),
			("c_max_q",		28,	20,	0),
			("c_deadtime",		37,	29,	1),
			("c_count",		41,	38,	0x0),
			("c_tac_max_age",	46,	42,	30),
			("c_tac_reset_len",	49,	47,	0b100),
			("c_wctrl_gate",	51,	51,	0b1),
			("c_branch_en",		53,	52,	0b11),
			("c_tac_rd_ext",	54,	54,	0),
			("c_sar_idle_limit",	60,	55,	36),
			("c_tac_stable_len",	63,	61,	0b100),
			("c_sar_sample_len",	66,	64,	0b011),
			("c_sar_wait",		67,	67,	0b1)
		]
		l_d3 = 68
		

		fields_d2 = [
			("c_tgr_main",		1,	0,	0b11),
			("c_tgr_t1",		3,	2,	0),
			("c_tgr_q",		5,	4,	0),
			("c_tgr_t2",		7,	6,	0),
			("c_tgr_V",		9,	8,	0),
			("c_tgr_B",		12,	10,	0)
		]
		l_d2 = 13
		
		
		fields_d1 = [
		]
		l_d1 = 0
		
		
		fields_a5 = [
			("sar_cfg_chn_mask",	0,	0,	0),
			("sar_cfg_delay9",	3,	1,	3),
			("sar_cfg_delay87",	6,	4,	3),
			("sar_cfg_delay65",	9,	7,	2),
			("sar_cfg_delay40",	12,	10,	1)
		]
		l_a5 = 13
		
		fields_a4 = [
			("cfg_a4_tac_2_trim",	5,	0,	24),
			("cfg_a4_tac_1_trim",	11,	6,	24)
		]
		l_a4 = 12
		
		fields_a3 = [
			("cfg_a3_vth_t1",	5,	0,	63),
			("cfg_a3_vth_t2",	11,	6,	63),
			("cfg_a3_vth_e",	17,	12,	63),
			("cfg_a3_delay_select",	20,	18,	0),
			("cfg_a3_vth_t_gain",	23,	21,	0b011)
		]
		l_a3 = 24
		
		fields_a2 = [
			("cfg_a2_attenuator_delay",	2,	0,	6),
			("cfg_a2_postamp_e_delay",	5,	3,	6),
			("cfg_a2_postamp_t_delay",	8,	6,	6),
			("cfg_a2_postamp_t_output_gain",11,	9,	0b010),
			("cfg_a2_attenuator_dc_cancel_en",12,	12,	1),
			("cfg_a2_postamp_e_output_gain",15,	13,	0b010),
			("cfg_a2_postamp_e_shapping",	17,	16,	0),
			("cfg_a2_postamp_power_down",	18,	18,	0),
			("cfg_a2_attenuator_gain",	21,	19,	0)
		]
		l_a2 = 22
		
		fields_a1 = [
			("cfg_a1_fetp_en",		0,	0,	0),
			("cfg_a1_gain",			1,	1,	0),
			("cfg_a1_power_down",		2,	2,	0)
		]
		l_a1 = 3


		l, f = compile_cfg_map (
			l_d3, fields_d3, l_d2,
			fields_d2, l_d1,
			fields_d1,
			l_a5, fields_a5, 
			l_a4, fields_a4,
			l_a3, fields_a3,
			l_a2, fields_a2,
			l_a1, fields_a1
		)

		self.l = l
		self.fields = {}
		for name, bits, default in f:
			self.fields[name] = bits

		if initial is not None:
			# We have an initial value, let's just go with it!
			self[0:self.l] = bitarray(initial)
			return None


		self[0:self.l] = bitarray(self.l)
		for name, bits, default in f:
			self.setValue(name, default)


		return None

	def __deepcopy__(self, memo):
		return AsicChannelConfig(initial=self)


## A class containing instances of AsicGlobalConfig and AsicChannelConfig
#, as well as 2 other bitarrays related to test pulse configuration. Is related to one given ASIC.
class AsicConfig:
	def __init__(self):
		self.channelConfig = [ AsicChannelConfig() for x in range(32) ]
		self.globalConfig = AsicGlobalConfig()
		self.globalConfigTX = AsicGlobalConfigTX()
		return None



class ConfigurationError(Exception):
	pass

class ConfigurationErrorStatus(ConfigurationError):
	def __init__(self, portID, slaveID, busID, chipID, value):
		self.addr = (value, portID, slaveID, busID, chipID)
	def __str__(self):
		return "Error 0x%02x when configuring ASIC at port %2d, slave %2d, bus %2d, chip %02d"  % self.addr

class ConfigurationErrorBadCRC(ConfigurationError):
	def __init__(self, portID, slaveID, asicID):
		self.addr = (portID, slaveID, asicID)
	def __str__(self):
		return "Received configuration datta with bad CRC from ASIC at port %2d, slave %2d, asic %2d" % self.addr

class ConfigurationErrorStuckHigh(ConfigurationError):
	def __init__(self, portID, slaveID, asicID):
		self.addr = (portID, slaveID, asicID)
	def __str__(self):
		return "MOSI stuck high from ASIC at port %2d, slave %2d, asic %2d" % self.addr

class ConfigurationErrorGeneric(ConfigurationError):
	def __init__(self, portID, slaveID, asicID, value):
		self.addr = (value, portID, slaveID, asicID)
	def __str__(self):
		return "Unexpected configuration error %02X from ASIC at port %2d, slave %2d, asic %2d" % self.addr

class ConfigurationErrorBadRead(ConfigurationError):
	def __init__(self, portID, slaveID, asicID, written, read):
		self.data = (portID, slaveID, asicID, written, read)
	def __str__(self):
		return "Configuration readback failed for ASIC at port %2d, slave %2d, asic %2d: wrote %s, read %s" % self.data

class ConfigurationErrorReplyLength(ConfigurationError):
	def __init__(self, expected, actual):
		self.data = (expected, actual)
	def __str__(self):
		return "Bad reply for ASIC configuration command: expected %d bytes, got %d bytes" % self.data


