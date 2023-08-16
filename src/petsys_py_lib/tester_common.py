
class Tester(object): pass

class TesterPowerException(Exception):
	def __init__(self, p, s, m, msg):
		self.__p = p
		self.__s = s
		self.__m = m
		self.__msg = msg

	def __str__(self):
		return "(%2d %2d %d) %s" % (self.__p, self.__s, self.__m, self.__msg)


