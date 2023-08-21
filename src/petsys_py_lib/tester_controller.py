import daqd, tester_common
import fe_tester
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

					else:
						print "ERROR: Unknown Tester at (%2d %2d %d): %s" % (portID, slaveID, module, adc_test_result)
						exit(1)



	def set_fe_power_all(self, mask):
		
		if (mask & 0b1) == 0:
			# Everything off
			for portID, slaveID in self.getActiveFEBDs():
				self.write_config_register(portID, slaveID, 8, 0x0213, 0b0)


		elif (mask & 0b10) == 0:
			# Power to Testers only
			# Disable 44 V and TEC source if enabled, leave only tester power
			print("tester power only")
			for portID, slaveID in self.getActiveFEBDs():
				pwr_en = 0b01
				self.write_config_register(portID, slaveID, 8, 0x0213, pwr_en)

			self.__identify_testers()
			for key, tester in sorted(self.__testers.items()):
				tester.set_uut_power(False)
		else:
			# Ensure low voltage on for Testers
			for portID, slaveID in self.getActiveFEBDs():
				pwr_en = self.read_config_register(portID, slaveID, 8, 0x0213)
				pwr_en |= 0b01
				self.write_config_register(portID, slaveID, 8, 0x0213, pwr_en)
			time.sleep(0.2)
			
			self.__identify_testers()

			try:
				for key, tester in sorted(self.__testers.items()):
					# Enable power to UUTs and perform basic power checks
					tester.set_uut_power(True)
			except tester_common.TesterPowerException as e:
				# There was a serious problem when powering up one of the testers
				# Cut all power and pass the exeption upstream
				self.write_config_register(portID, slaveID, 8, 0x0213, 0)
				raise e

			# Finally turn the 44 V source
			for portID, slaveID in self.getActiveFEBDs():
				self.write_config_register(portID, slaveID, 8, 0x0213, 0b0101)
		

	def set_fe_power(self, on):
		if not on:
			self.set_fe_power_all(0b01)
		else:
			self.set_fe_power_all(0b11)
			
			
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
		return self.__testers

