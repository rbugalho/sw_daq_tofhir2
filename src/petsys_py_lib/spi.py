import time

def spi_reg_ll(conn, portID, slaveID, chipID, data_out):
	p = 2
	padding = [ 0xFF for n in range(p) ]
	p = 8 * p
	w = len(data_out) * 8

	# Pad the cycle with zeros
	return conn.spi_master_execute(portID, slaveID, 0x02, chipID,
		p+w+p,          # cycle
		p,p+w,          # sclk en
		p-1,p+w+1,      # cs
		0, p+w+p,       # mosi
		p,p+w,
		padding + data_out + padding)

def spi_reg(conn, portID, slaveID, chipID, l, data_out):
	data_out = [ (data_out >> k) & 0xFF for k in range(0, l, 8) ]
	data_out = data_out[::-1]


	r = spi_reg_ll(conn, portID, slaveID, chipID, data_out)


	r = r[1:-1]
	#print(r)
	r = [ v << (l - 8 - 8*k) for k, v in enumerate(r) ]
	r = sum(r)

	return r

def dac_ll(conn, portID, slaveID, chipID, command):
        w = 8 * len(command)
        padding = [0xFF for n in range(1) ]
        p = 8 * len(padding)

        # Pad the cycle with zeros
        return conn.spi_master_execute(portID, slaveID, 0x02, chipID,
                p+w+p,          # cycle
                p,p+w,          # sclk en
                p-1,p+w+1,      # cs
                0, p+w+p,       # mosi
        	p,p+w,      # miso
                padding + command + padding)

def dac_set(conn, portID, slaveID, spi_id, dac_channel, dac_amplitude):
	dac_high, dac_low = dac_amplitude >> 8, dac_amplitude & 0xFF
	wrt_trg_command = [ 0b00110000 | (1 << dac_channel), dac_high, dac_low ]
	dac_ll(conn, portID, slaveID, spi_id, wrt_trg_command)


def ad7738_ll(conn, portID, slaveID, chipID, command):
	command = [ command ]
        w = 8 * len(command)
        padding = [0xFF for n in range(1) ]
        p = 8 * len(padding)

        # Pad the cycle with zeros
        return conn.spi_master_execute(portID, slaveID, 0x02, chipID,
                p+w+p,          # cycle
                p,p+w,          # sclk en
                p-1,p+w+1,      # cs
                0, p+w+p,       # mosi
        	p,p+w,      # miso
                padding + command + padding)

def ad7738_set_register(conn, portID, slaveID, chipID, register, value):
	ad7738_ll(conn, portID, slaveID, chipID, 0b00000000 | register)
	ad7738_ll(conn, portID, slaveID, chipID, value)

def ad7738_get_register(conn, portID, slaveID, chipID, register, l=1):
	r= ad7738_ll(conn, portID, slaveID, chipID, 0b01000000 | register)
	retval = 0
	for k in range(l):
		r = ad7738_ll(conn, portID, slaveID, chipID, 0x00)
		retval = retval * 256 + r[1]

	return retval

def ad7738_check(conn, portID, slaveID, chipID):
	u = ad7738_get_register(conn, portID, slaveID, chipID, 0x02)
	u = ad7738_get_register(conn, portID, slaveID, chipID, 0x02)
	return u == 0x21

def ad7738_read_channel(conn, portID, slaveID, chipID, ch):
	ad7738_check(conn, portID, slaveID, chipID)

	ad7738_set_register(conn, portID, slaveID, chipID, 0x28 + ch, 0b00001101)
	ad7738_set_register(conn, portID, slaveID, chipID, 0x38 + ch, 0b01000010)

	time.sleep(0.1)
	status = ad7738_get_register(conn, portID, slaveID, chipID, 0x20+ ch)
	val = ad7738_get_register(conn, portID, slaveID, chipID, 0x08 + ch, l=3)
	#print status >> 5, status & 0b1000, status & 0b100, status & 0b10, status & 0b1, "0x%012X" % val, 1.25 / (2**23) * val
	return val

	
	

class MAX111xxError(Exception): pass

def max111xx_ll(conn, portID, slaveID, chipID, command):
        w = 8 * len(command)
        padding = [0xFF for n in range(2) ]
        p = 8 * len(padding)

        # Pad the cycle with zeros
        return conn.spi_master_execute(portID, slaveID, 0x02, chipID,
                p+w+p,          # cycle
                p,p+w,          # sclk en
                0,p+w+p,        # cs
                0, p+w+p,       # mosi
                p,p+w,          # miso
                padding + command + padding
	)

def max111xx_check(conn, portID, slaveID, chipID):
        m_config1 = 0x00008064  # single end ref; no avg; scan 16; normal power; echo on
        m_config2 = 0x00008800  # single end channels (0/1 -> 14/15, pdiff_com)
        m_config3 = 0x00009000  # unipolar convertion for channels (0/1 -> 14/15)
        m_control = 0x00000826  # manual external; channel 0; reset FIFO; normal power; ID present; CS control

        reply = max111xx_ll(conn, portID, slaveID, chipID, [(m_config1 >> 8) & 0xFF, m_config1 & 0xFF])
        reply = max111xx_ll(conn, portID, slaveID, chipID, [(m_config2 >> 8) & 0xFF, m_config2 & 0xFF])
        reply = max111xx_ll(conn, portID, slaveID, chipID, [(m_config3 >> 8) & 0xFF, m_config3 & 0xFF])
        if reply[1] == 0xFF and reply[2] == 0xFF:
                return False

        if not (reply[1] == 0x88 and reply[2] == 0x0):
                return False

        reply = max111xx_ll(conn, portID, slaveID, chipID, [(m_control >> 8) & 0xFF, m_control & 0xFF])
        if not(reply[1] == 0x90 and reply[2] == 0x0):
                return False

        return True

def max111xx_read(conn, portID, slaveID, chipID, channelID):
        m_control = 0x00000826  # manual external; channel 0; reset FIFO; normal power; ID present; CS control
        m_repeat = 0x00000000

        command = m_control + (channelID << 7)
        reply = max111xx_ll(conn, portID, slaveID, chipID, [(command >> 8) & 0xFF, command & 0xFF])
        reply = max111xx_ll(conn, portID, slaveID, chipID, [(m_repeat >> 8) & 0xFF, m_repeat & 0xFF])
        v = reply[1] * 256 + reply[2]
        u = v & 0b111111111111
        ch = (v >> 12)
	if ch != channelID: raise MAX111xxError("Error reading (%2d %2d) chip 0x%04X channel %2d" % (portID, slaveID, chipID, channelID))
        return u
