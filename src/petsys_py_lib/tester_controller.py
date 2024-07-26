import daqd, tester_common, tofhir2b
import fe_tester, bga_tester
import spi, i2c
import time

class Connection(daqd.Connection):

	def __init__(self):
		super(Connection, self).__init__()

		self.__testers = {}

	def __identify_testers(self):
			# Identify Tester Modules
			self.__testers = {}
			for portID, slaveID in self.getActiveFEBDs():
				for module in range(8):
					adc_test_result = [ spi.max111xx_check(self, portID, slaveID, 0x10 * (module+1) + chip_id) for chip_id in range(0x3, 0xA) ]

					if adc_test_result == [ False, False, False, False, False, False, False ]:
						# This port seems empty
						continue
					elif adc_test_result == [ True, True, True, True, True, True, True ]:
						# This port seems to have a FE tester
						self.__testers[(portID, slaveID, module)] = fe_tester.Tester(self, portID, slaveID, module)

					elif adc_test_result == [False, False, True, False, False, False, False]:
						# This port may have a BGA tester
						self.__testers[(portID, slaveID, module)] = bga_tester.Tester(self, portID, slaveID, module)

					else:
						print "ERROR: Unknown Tester at (%2d %2d %d): %s" % (portID, slaveID, module, adc_test_result)
						exit(1)



	def set_uut_power(self, on):
		# Always ensure controller is providing all power rails to testers
		wait_for_power = False
		for portID, slaveID in self.getActiveFEBDs():
			pwr_en = self.read_config_register(portID, slaveID, 8, 0x0213)
			if (pwr_en & 0b11) != 0b11:
				wait_for_power = True
				
			self.write_config_register(portID, slaveID, 8, 0x0213, 0b11)
				
		if wait_for_power:
			# If a FEB/D was powered off wait for a second for power to stabilize
			# and Tester FPGAs to boot
			time.sleep(1.0)

		wait_for_power = False
		for key, tester in self.get_testers().items():
				pwr_en = tester.get_uut_power()
				if pwr_en is False and on:
					wait_for_power = True
					
				tester.set_uut_power(on)
			
		if wait_for_power:
			time.sleep(1.0)
			
			
	def set_48V_power(self, on):
		for portID, slaveID in self.getActiveFEBDs():
			pwr_en =  self.read_config_register(portID, slaveID, 8, 0x0213)
			if not on:
				pwr_en &= ~0b0100
				self.write_config_register(portID, slaveID, 8, 0x0213, pwr_en)
			else:
				pwr_en |= 0b0100
				self.write_config_register(portID, slaveID, 8, 0x0213, pwr_en)
				time.sleep(0.2)

	def set_tec_power(self, on):
		for portID, slaveID in self.getActiveFEBDs():
			pwr_en =  self.read_config_register(portID, slaveID, 8, 0x0213)
			if not on:
				pwr_en &= ~0b1000
				self.write_config_register(portID, slaveID, 8, 0x0213, pwr_en)
			else:
				pwr_en |= 0b1000
				self.write_config_register(portID, slaveID, 8, 0x0213, pwr_en)
				time.sleep(0.2)

		
		


	def get_testers(self):
		if self.__testers == {}:
			self.__identify_testers()
		return self.__testers

	def initialize_burn_in(self):
		self.__asic_module = tofhir2b
		self.set_fe_power(True)

		# Reset the ASICs configuration
		for portID, slaveID in self.getActiveFEBDs(): self.write_config_register(portID, slaveID, 2, 0x0201, 0b00)
		for k in range(10):
			# Generate multiple resets to train the RESYNC receiver
			for portID, slaveID in self.getActiveFEBDs(): self.write_config_register(portID, slaveID, 1, 0x300, 0b1)
			for portID, slaveID in self.getActiveFEBDs(): self.write_config_register(portID, slaveID, 1, 0x300, 0b0)

		for portID, slaveID in self.getActiveFEBDs():
			tdc_clk_div, ddr, tx_nlinks = self.__getAsicLinkConfiguration(portID, slaveID)
			gctx = self.__asic_module.AsicGlobalConfigTX()
			c_tx_mode = 0b0000

			# Select DDR mode
			if ddr:
				c_tx_mode |= 0b1000
			else:
				c_tx_mode |= 0b0000

			gctx.setValue("c_tx_mode", c_tx_mode)
			gctx.setValue("c_tx_clps", 1023)

			gc = self.__asic_module.AsicGlobalConfig()
			gc.setValue("Iref_cal_DAC", 187)

			cc = self.__asic_module.AsicChannelConfig()

			for attempt in range(4):
				for chipID in range(32):
					for busID in range(8):
						self.__tofhir2_cmd(portID, slaveID, busID, chipID, 2*busID+chipID, 33, True, False, gctx)
						self.__tofhir2_cmd(portID, slaveID, busID, chipID, 2*busID+chipID, 32, True, False, gc)
						for channelID in range(32):
							self.__tofhir2_cmd(portID, slaveID, busID, chipID, 2*busID+chipID, channelID, True, False, cc)

		return None
