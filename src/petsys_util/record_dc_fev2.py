#!/usr/bin/env python

import sys
from petsys import daqd, tofhir2
from time import sleep
import bitarray
from copy import deepcopy
import serial
#import sefram
import os.path

def read_multimeter(port):
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



def set_monitor_mux(conn, mux_sel):
	asicsConfig = conn.getAsicsConfig()
	for ac in asicsConfig.values():
		gc = ac.globalConfig
		gc.setValue("MUX_EN", 1)
		gc.setValue("MUX_SEL", mux_sel)
	conn.setAsicsConfig(asicsConfig)
	return None
	
	
def scan_global(conn, multimeter, file_name, cfg_name, cfg_min, cfg_max, cfg_step):
	print "Scanning %s [%d, %d]" % (cfg_name, cfg_min, cfg_max)
	output_file = open(file_name, "w")
	
	read_multimeter(multimeter)
	for cfg_value in range(cfg_min, cfg_max, cfg_step):
		asicsConfig = conn.getAsicsConfig()
		for ac in asicsConfig.values():
			gc = ac.globalConfig
			gc.setValue(cfg_name, cfg_value)
		
		conn.setAsicsConfig(asicsConfig)
		voltage = read_multimeter(multimeter)
		
		print "%3d -> %6.4f" % (cfg_value, voltage)
		output_file.write("%d\t%f\n" % (cfg_value, voltage))
	
	output_file.close()
	return None

def scan_ch15(conn, multimeter, file_name, cfg_name, cfg_min, cfg_max, cfg_step):
	
	print "Scanning %s [%d, %d]" % (cfg_name, cfg_min, cfg_max)
	output_file = open(file_name, "w")
	
	read_multimeter(multimeter)
	for cfg_value in range(cfg_min, cfg_max, cfg_step):
		asicsConfig = conn.getAsicsConfig()
		for ac in asicsConfig.values():
			cc = ac.channelConfig[15]
			cc.setValue(cfg_name, cfg_value)
		
		conn.setAsicsConfig(asicsConfig)
		voltage = read_multimeter(multimeter)
		
		print "%3d -> %6.4f" % (cfg_value, voltage)
		output_file.write("%d\t%f\n" % (cfg_value, voltage))
	
	output_file.close()
	return None

	
def main(argv):
	dir_name = argv[2]
	
	
	conn = daqd.Connection()
	conn.initializeSystem()
	
	multimeter = serial.Serial(argv[1], 9600, timeout=1, bytesize=8, parity='N', stopbits=1)
	#multimeter = sefram.Sefram(argv[1])
	
	

	asicsConfig0 = deepcopy(conn.getAsicsConfig())

	activeAsics = [ a for p,s,a in conn.getActiveAsics() ]
	activeBoards = set([ a // 2 for a in activeAsics ])
	activeBoards = list(activeBoards)

	for board in activeBoards:
		print "CONNECT CABLE TO BOARD at port %d" % board
		raw_input("Press ENTER to continue")

		for chipID in [ 2*board + n for n in range(0, 2) ]:
			if chipID not in activeAsics: continue


			output_file = open(os.path.join(dir_name, "A%d_current_trim.txt" % chipID), "w")
			output_file.write("%d\n" % asicsConfig0[(0, 0, chipID)].globalConfig.getValue("Iref_cal_DAC"))


			print "CONNECT MULTIMETER TO ASIC %d BANDGAP" % chipID
			print "Check voltage is ~250-350 mV (press 'Local' if needed)"
			raw_input("Press ENTER to continue")

			conn.setAsicsConfig(asicsConfig0)
			output_file = open(os.path.join(dir_name, "A%d_bandgap.txt" % chipID), "w")
			voltage = read_multimeter(multimeter)
			print "Bandgap voltage = %4.4f V" % voltage
			output_file.write("%f\n" % voltage)
			output_file.close()


			conn.setAsicsConfig(asicsConfig0)
			set_monitor_mux(conn, 0)
			print "CONNECT MULTIMETER TO ASIC %d MONITOR" % chipID
			print "Check voltage is ~700-800 mV (press 'Local' if needed)"
			raw_input("Press ENTER to continue")

			conn.setAsicsConfig(asicsConfig0)
			set_monitor_mux(conn, 1)
			scan_global(conn, multimeter, os.path.join(dir_name, "A%d_TAC_QAC_Vbl.txt" % chipID), "TAC_QAC_Vbl_DAC", 0, 64, 1)

			conn.setAsicsConfig(asicsConfig0)
			set_monitor_mux(conn, 2)
			scan_global(conn, multimeter, os.path.join(dir_name, "A%d_SE2Diff_CM.txt" % chipID), "SE2Diff_CM_DAC", 0, 64, 1)

			#print "CONNECT MULTIMETER TO V_ALDO A (III)"
			#print "Check voltage is 750-850 mV (press 'Local' if needed)"
			#raw_input("Press ENTER to continue")

			#asicsConfig = deepcopy(asicsConfig0)
			#for aldo_gain in [0, 1]:
				#print ">> ALDO DAC gain = %d" % aldo_gain
				#for ac in asicsConfig.values():
					#ac.globalConfig.setValue("Valdo_A_Gain", aldo_gain)
				#conn.setAsicsConfig(asicsConfig)
				#scan_global(conn, multimeter, os.path.join(dir_name, "A%d_Valdo_A_gain_%d.txt" % (chipID, aldo_gain)), "Valdo_A_DAC", 0, 256, 1)

			#print "CONNECT MULTIMETER TO V_ALDO B (IIII)"
			#print "Check voltage is 750-850 mV (press 'Local' if needed)"
			#raw_input("Press ENTER to continue")

			#asicsConfig = deepcopy(asicsConfig0)
			#for aldo_gain in [0, 1]:
				#print ">> ALDO DAC gain = %d" % aldo_gain
				#for ac in asicsConfig.values():
					#ac.globalConfig.setValue("Valdo_B_Gain", aldo_gain)
				#conn.setAsicsConfig(asicsConfig)
				#scan_global(conn, multimeter, os.path.join(dir_name, "A%d_Valdo_B_gain_%d.txt" % (chipID, aldo_gain)), "Valdo_B_DAC", 0, 256, 1)
	
	
	
	
	return 0
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
