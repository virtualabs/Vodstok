def to_hex(s):
	"""
	String to hex
	"""
	return ''.join(['%02X'%ord(c) for c in s])
	
def from_hex(h):
	"""
	Hex to string
	"""
	return ''.join(['%c'%(int(h[i*2:(i+1)*2],16)) for i in range(len(h)/2)])
	
def convert_bytes(bytes):
	"""
	Python recipe from http://www.5dollarwhitebox.org/drupal/node/84
	"""
	bytes = float(bytes)
	if bytes >= 1099511627776:
		terabytes = bytes / 1099511627776
		size = '%.2f TB' % terabytes
	elif bytes >= 1073741824:
		gigabytes = bytes / 1073741824
		size = '%.2f GB' % gigabytes
	elif bytes >= 1048576:
		megabytes = bytes / 1048576
		size = '%.2f MB' % megabytes
	elif bytes >= 1024:
		kilobytes = bytes / 1024
		size = '%.2f KB' % kilobytes
	else:
		size = '%.2f B' % bytes
	return size

def formatSpeed(s):
	if s>2**30:
		return '%0.2f Gb/s' % (float(s)/2**30)
	elif s>2**20:
		return '%0.2f Mb/s' % (float(s)/2**20)
	elif s>2**10:
		return '%0.2f Kb/s' % (float(s)/2**10)
	else:
		return '%d b/s' % s
