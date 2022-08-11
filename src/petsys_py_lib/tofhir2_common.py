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
				sys.stderr.write("ERROR in field %s: bits %s already used\n"  % (name, (", ").join([str(b) for b in intersection])))
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

	def __str__(self):
		s = str(bitarray(self))

		s = s[10:]
		s = s[:-2]
		s = "%d'b%s" % (len(s), s)
		return s
		

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


