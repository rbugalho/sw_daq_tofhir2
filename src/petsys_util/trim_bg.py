#!/usr/bin/env python

import sys
from petsys import daqd, tofhir2
from time import sleep
import bitarray
from copy import deepcopy
import serial
#import sefram

def read_multimeter(port):
	sleep(0.5)
	port.write(':MEAS:VOLT:DC? \r')
	port.flush(); sleep(0.1)
	reply = port.read(16)

	sleep(0.5)
	port.write(':MEAS:VOLT:DC? \r')
	port.flush(); sleep(0.1)
	reply = port.read(16)
	reply = reply[:-1]
	v = float(reply)
	return v
	
	#sleep(0.5)
	#v = port.getValue() * 1E4
	#return v

def log(f, s):
	f.write(s)
	f.write('\n')
	print s

def main(argv):
	conn = daqd.Connection()
	#conn.initializeSystem()
	
	
	portID = 0
	slaveID = 0
	chipID = int(argv[1])	# 0 is A0, 1 is A1, ...
	busID = chipID / 2
	chipID = chipID % 2
	output_file = open(argv[2], "w")
	
	multimeter = serial.Serial(argv[3], 9600, timeout=1, bytesize=8, parity='N', stopbits=1)
	#multimeter = sefram.Sefram(argv[3])

	conn.write_config_register_febds(3, 0x0213, 0b111)
	sleep(1.0)	
	
	# Load bandgap
	conn._Connection__tofhir2_cmd(portID, slaveID, busID, chipID, 35, True, False, bitarray.bitarray(254))
	sleep(0.1)
	conn._Connection__tofhir2_cmd(portID, slaveID, busID, chipID, 36, True, False, bitarray.bitarray(254))
	sleep(0.1)

	
	trim_options = { 
		7	: -12.28E-3,
		6	: -12.32E-3,
		5	: -12.34E-3,
		4	: +19.27E-3,
		3	: +9.73E-3,
		2	: +4.89E-3,
		1	: +2.49E-3,
		0	: +1.25E-3,
		None	: 0
	}
	
	target = 0.300
	
	print("T2TB: SET VFUSE JUMPER TO 2V5")
	print("FEv2: SET RX&EFUSE [5:6] to OFF OFF")
	
	value = read_multimeter(multimeter)
	log(output_file, "INITIAL VALUE: %1.5f" % value)
	while abs(value - target) > 0.7E-3:
		selected_option = None
		expected_voltage = value + 1E6
		selected_option_error = abs(value - target)
		
		for option, delta in trim_options.items():

			# If current value is above target + 4 mV, consider only negative trim options
			if (value > (target + 4e-3)) and (delta >= 0): continue
			
			option_error = abs(value + delta - target)
			if option_error < selected_option_error:
				selected_option_error = option_error
				selected_option = option
				expected_voltage = value + delta
		
		if selected_option is None: break
		
		log(output_file, "SELECTED %d (%1.5f), EXPECT %1.5f" % (selected_option, trim_options[selected_option], expected_voltage))
		gc = tofhir2.AsicGlobalConfig()
		gc.setValue("EFUSE_A", selected_option)
		conn._Connection__tofhir2_cmd(portID, slaveID, busID, chipID, 32, True, False, gc)		
		
		answer = raw_input("Proceed? (Y/N)")
		if answer.lower() != 'y':
			break
		
		del trim_options[selected_option]
		
		
		# Trim
		conn._Connection__tofhir2_cmd(portID, slaveID, busID, chipID, 37, True, False, bitarray.bitarray(160))
		sleep(0.1)
		
		# Load
		conn._Connection__tofhir2_cmd(portID, slaveID, busID, chipID, 35, True, False, bitarray.bitarray(254))
		sleep(0.1)
		conn._Connection__tofhir2_cmd(portID, slaveID, busID, chipID, 36, True, False, bitarray.bitarray(254))
		sleep(0.1)
	
		value = read_multimeter(multimeter)
		log(output_file, "NEW VALUE. %1.5f" % value)

	print("T2TB: SET VFUSE JUMPER TO 1V2")
	
	return 0
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
