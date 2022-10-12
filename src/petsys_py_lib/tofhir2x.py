# -*- coding: utf-8 -*-
from bitarray import bitarray
from bitarray_utils import intToBin, binToInt, grayToBin, grayToInt
import sys
from .tofhir2 import *

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
			("c_int_tp_delay", 5, 3, 0),
			("g_cfg_tp2_en", 6, 6, 0),
			("g_cfg_tp2_inv", 7, 7, 0),
			("g_cfg_tp2_period", 17, 8, 0),
			("g_cfg_tp2_length", 27, 18, 0),
			("g_cfg_tp2_clk", 28, 28, 0)
		]
		l_d2 = 29

		fields_mb = [
			("Enable_baseline_T_mirrors", 0, 0, 1),
			("Baseline_T_DAC", 6, 1, 32),
			("Enable_preamp_mirrors", 7, 7, 1),
			("Preamp_bias_DAC", 13, 8, 32),
			("Enable_discriminator_mirrors", 14, 14, 1),
			("Discriminator_bias_DAC", 20, 15, 32),
			("Enable_baseline_E_mirrors", 21, 21, 1),
			("Baseline_E_DAC", 27, 22, 32),
			("Enable_TAC1_mirrors", 28, 28, 1),
			("TAC1_bias_DAC", 34, 29, 32),
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
			("c_tx_clps",	13,	4,	0x3FF),
			("c_dual",	14,	14,	0)
		]
		l_d3 = 15


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
			("c_tac_max_age",	46,	42,	29),
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
		
		fields_a123 = [
			("cfg_a3_delay_select", 2, 0, 1 ),
			("cfg_a3_ith_t1", 8, 3, 31),
			("cfg_a3_ith_t2", 14, 9, 44),
			("cfg_a3_ith_e", 20, 15, 10),
			("cfg_a2_attenuator_dc_cancel_en", 21, 21, 1),
			("cfg_a2_attenuator_gain", 24, 22, 7),
			("cfg_a3_range_t1", 26, 25, 1),
			("cfg_a3_range_t2", 28, 27, 0),
			("cfg_a3_range_e", 30, 29, 0),
			("cfg_a2_dcr_delay_t", 38, 31, 0b00001111),
			("cfg_a2_dcr_delay_e", 45, 39, 0b0001111),
			("cfg_a2_pulse_trim_t", 50, 46, 15),
			("cfg_a2_pulse_trim_e", 55, 51, 19),
			("cfg_a1_fetp_en", 56, 56, 0),
			("cfg_a1_power_down", 57, 57, 0)
		]
		l_a123 = 58
		

		l, f = compile_cfg_map (
			l_d3, fields_d3, l_d2,
			fields_d2, l_d1,
			fields_d1,
			l_a5, fields_a5, 
			l_a4, fields_a4,
			l_a123, fields_a123
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


