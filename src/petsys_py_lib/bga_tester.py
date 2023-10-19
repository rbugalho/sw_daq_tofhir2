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
			# Disable everything except the LEDs
			self.__cfg &= 0b111111
			spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)

		else:
			vin = self.get_tester_vin()
			if vin < 1.6:
				raise TesterPowerException(self.__p, self.__s, self.__m, "Tester input voltage %4.2f V is under 1.6 V" % vin)
			if vin > 2.5:
				raise TesterPowerException(self.__p, self.__s, self.__m, "Tester input voltage %4.2f V is above 2.5 V" % vin)


			# Enable ASICs, one at a time
			for k in range(2):
				mask = 0b1 << (6+k)
				self.__cfg |= mask
				spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)

				iin = self.get_uut_iin(k)
				if iin > 0.5:
					#raise TesterPowerException(self.__p, self.__s, self.__m, "ASIC %d input current %4.2f is above 0.5 A" % (k, iin))
					print "WARNING: Tester (%d, %d, %d) ASIC %d input current is above 0.5 A and will be disabled" % (self.__p, self.__s, self.__m, k, iin)
					self.__cfg &= (~mask)
					spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)
					continue


				vin = self.get_uut_vin(k)
				if abs(vin - 1.2) > 0.06:
					raise TesterPowerException(self.__p, self.__s, self.__m, "ASIC %d input voltage %4.2f is abnormal" % (k, vin))



			# Disable reset
			self.__cfg |= (0b11 << 8)
			# Enable injector power
			self.__cfg |= (0b1 << 34)
			spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)
				

	def __adc_read(self, chip_id, channel_id):
		if chip_id == 0x5:
			M = 2.048 / 4096
			u = spi.max111xx_read(self.__conn, self.__p, self.__s, 0x10*(self.__m+1) + chip_id, channel_id)
			return M * u

		else:
			M = 1.25 / (2**23)
			u = spi.ad7738_read_channel(self.__conn, self.__p, self.__s, 0x10*(self.__m+1) + chip_id, channel_id)
			return M * u


	def get_tester_vin(self):
		return 3.0 * self.__adc_read(0x5, 0)

	def get_uut_vin(self, k):
		adc_map = { 0: 2, 1: 1 }
		return self.__adc_read(0x5, adc_map[k])

	def get_uut_iin(self, k):
		adc_map = { 0: 4, 1: 3 }
		return 0.5 * self.__adc_read(0x5, adc_map[k])

	def get_uut_vbg(self, k):
		return self.__adc_read(0x3 + k, 0)

	def set_leds(self, k, value):
		mask = 0b111 << 3*k
		self.__cfg &= ~mask
		self.__cfg |= value << (3*k)
		spi.spi_reg(self.__conn, 0, 0, 0x10*(self.__m+1)+0, 64, self.__cfg)



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




INJECTOR_CHANNEL_MAP = {
	0	: 6,
	1	: 5,
	2	: 3,
	3	: 7,
	4	: 4,
	5	: 12,
	6	: 2,
	7	: 1,
	8	: 14,
	9	: 0,
	10	: 11,
	11	: 13,
	12	: 15,
	13	: 8,
	14	: 10,
	15	: 9,
	16	: 21,
	17	: 20,
	18	: 22,
	19	: 23,
	20	: 19,
	21	: 17,
	22	: 28,
	23	: 18,
	24	: 26,
	25	: 25,
	26	: 16,
	27	: 29,
	28	: 30,
	29	: 24,
	30	: 27,
	31	: 31
}

