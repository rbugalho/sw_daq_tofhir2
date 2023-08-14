from tester_common import TesterPowerException
import spi
import time

class Tester(object):
	def __init__(self, conn, p, s, m):
		self.__conn = conn
		self.__p = p
		self.__s = s
		self.__m = m
		self.__cfg = 0x0

	def set_uut_power(self, on):
		if not on:
			self.__cfg &= ~0b111100
			spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)

		else:
			vin = self.get_tester_vin()
			if vin < 1.6:
				raise TesterPowerException(self.__p, self.__s, self.__m, "Tester input voltage %3.1f V is under 1.6 V" % vin)
			if vin > 2.5:
				raise TesterPowerException(self.__p, self.__s, self.__m, "Tester input voltage %3.1f V is above 2.5 V" % vin)

			self.__cfg |= 0b111100
			spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)
			time.sleep(0.1)
		
			# Check current and voltages
			vin = self.get_tester_vin()
			if vin < 1.6:
				raise TesterPowerException(self.__p, self.__s, self.__m, "Tester input voltage %3.1f V is under 1.6 V" % vin)

			vin = self.get_uut_vin()
			if vin < 1.6:
				raise TesterPowerException(self.__p, self.__s, self.__m, "UUT input voltage %3.1f V is under 1.6 V" % vin)

			iin = self.get_uut_iin()
			if iin > 1.0:
				raise TesterPowerException(self.__p, self.__s, self.__m, "UUT input current %3.1f A is above 1.0 A" % iin)
	

			#for n in range(2):
				#v = self.get_uut_1V2(n)
				#if abs(1.2 - v) > 0.12:
					#raise TesterPowerException(self.__p, self.__s, self.__m, "UUT ASIC %d VDD %4.2f V is outside tolerance" % (n, v))
	
				

	def __adc_read(self, chip_id, channel_id):
		M = 2.048 / 4096
		u = spi.max111xx_read(self.__conn, self.__p, self.__s, 0x10*(self.__m+1) + chip_id, channel_id)
		return M * u


	def get_tester_vin(self):
		return 3.0 * self.__adc_read(0x4, 0)

	def get_uut_vin(self):
		return 3.0 * self.__adc_read(0x4, 1)

	def get_uut_iin(self):
		return  self.__adc_read(0x4, 12)

	def get_uut_1V2(self, n):
		return  self.__adc_read(0x4, 2+n)


	def get_tec_resistance(self, detailed=False):
		vi = self.__adc_read(0x4, 7)
		vo = self.__adc_read(0x4, 6)


		if vo < 0.010:
			if not detailed:
				return 1E6
			else:
				return  [ 1E6 for n in range(4) ]


		r_cable = 1 /(vo/(1-vi) -1)
		i_test = (1 - vi)/r_cable

		if not detailed:
			r_uut = (vi - vo)/i_test
			return r_uut
		else:
			vx = [ self.__adc_read(0x3, n) for n in [ 3, 0, 2, 1 ] ]
			vx += [ vo ]
			r_x = [ (vx[n] - vx[n+1])/i_test  for n in range(4) ]
			return r_x


	def get_pt1000_resistance(self):
		vi = self.__adc_read(0x4, 9)
		vo = [ self.__adc_read(0x4, n) for n in [ 8, 10, 14, 15 ] ]

		io = [ v / 12.0 for v in vo ]

		ro = [1E6 for n in range(4) ]
		for n in range(4):
			if io[n] != 0:
				ro[n] = (vi - vo[n])/io[n]

		return ro


	def enable_bias_voltage_load(self, on):
		if on:
			self.__cfg |= 0b1111000000
		else:
			self.__cfg &= ~0b1111000000

		spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)

	# Returns bias voltage reads from ADC
	# @param asic ASIC to be read
	# @param aOrB ALDO to be read
	# @param single_read Return only a read from the primary read point or 18 reads from the 18 test points
	def __get_bias_voltage(self, asic, aOrB, single_read=True):
		k1 = (20E3+549E3)/20E3
		k2 = (20E3+510E3)/20E3

		adc_channel_map = {
			(0, "A") : [ (0x3, 9, k1), (0x3, 7, k2) ] + [ (0x6, n, k2) for n in range(16) ],
			(0, "B") : [ (0x3, 8, k1), (0x3, 6, k2) ]+ [ (0x7, n, k2) for n in range(16) ],
			(1, "A") : [ (0x3, 10, k1), (0x3, 5, k2) ]+ [ (0x8, n, k2) for n in range(16) ],
			(1, "B") : [ (0x3, 11, k1), (0x3, 4, k2) ]+ [ (0x9, n, k2) for n in range(16) ],
			}

		adc_channels = adc_channel_map [(asic, aOrB.upper())]

		if single_read:
			chip, channel, k = adc_channels[0]
			return self.__adc_read(chip, channel) * k

		else:
			return [ self.__adc_read(chip, channel) * k for chip, channel, k in adc_channels ]


	# Returns bias voltage reads from ADC
	# @param asic ASIC to be read
	# @param aOrB ALDO to be read
	def get_bias_voltage(self, asic, aOrB):
		return self.__get_bias_voltage(asic, aOrB, single_read=True)

	# Returns list of test points whose voltage is outside expected
	# @param asic ASIC to be read
	# @param aOrB ALDO to be read
	def check_bias_voltage(self, asic, aOrB, expected):
		# First two measurements are taken from dividers with 0.1% tolerance resistors
		# Last 16 measurements are taken from diviers with 1% tolerance resistors
		tolerance = [ 0.05, 0.05 ] + [ 0.5 for k in range(16) ]

		values = self.__get_bias_voltage(asic, aOrB, single_read=False)
		#print [ v - expected for v in values ]
		failed = [ k for k, v in enumerate(values) if abs(v - expected) > tolerance ]
		return failed



	def get_bias_current(self, asic, aOrB, single_read=True):
		adc_channel_map = {
			(0, "A") : 0,
			(0, "B") : 1,
			(1, "A") : 2,
			(1, "B") : 3
			}

		adc_channel = adc_channel_map[(asic, aOrB)]

		return self.__adc_read(0x5, adc_channel) / 17.8E3


	def injector_disable(self):
		self.__cfg &= ~0b1111111111111110000000000000000000
		spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)

		spi.dac_set(self.__conn, 0, 0, 0x10*(self.__m+1) + 2, 0, 0x8000)
		spi.dac_set(self.__conn, 0, 0, 0x10*(self.__m+1) + 2, 1, 0x8000)


	def injector_enable(self, channel, amplitude):
		channel = INJECTOR_CHANNEL_MAP[channel]

		mux_a = channel & 0x7
		mux_sel = 1 << (channel >> 3)

		# Clear all injector bits
		self.__cfg &= ~0b1111111111111110000000000000000000

		self.__cfg |= 0b1100 << 19
		self.__cfg |= mux_a << 23
		self.__cfg |= mux_sel << 26
		self.__cfg |= mux_sel << 30
		spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)

		spi.dac_set(self.__conn, 0, 0, 0x10*(self.__m+1) + 2, 0, amplitude)
		spi.dac_set(self.__conn, 0, 0, 0x10*(self.__m+1) + 2, 1, amplitude)




INJECTOR_CHANNEL_MAP = {0: 26, 1: 25, 2: 31, 3: 27, 4: 24, 5: 16, 6: 30, 7: 29, 8: 18, 9: 28, 10: 23, 11: 17, 12: 19, 13: 20, 14: 22, 15: 21, 16: 9, 17: 8, 18: 10, 19: 11, 20: 15, 21: 13, 22: 0, 23: 14, 24: 6, 25: 5, 26: 12, 27: 1, 28: 2, 29: 4, 30: 7, 31: 3}


INJECTOR_CHANNEL_MAP2 = {
	0: 22,
	1: 27,
	2: 28,
	3: 31,
	4: 29,
	5: 25,
	6: 24,
	7: 30,
	8: 17,
	9: 16,
	10: 18,
	11: 19,
	12: 26,
	13: 21,
	14: 23,
	15: 20,
	16: 5,
	17: 11,
	18: 8,
	19: 12,
	20: 13,
	21: 15,
	22: 14,
	23: 10,
	24: 4,
	25: 1,
	26: 0,
	27: 3,
	28: 9,
	29: 7,
	30: 6,
	31: 2
}

