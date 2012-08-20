"""
Vodstok helpers
"""

from urlparse import urlparse

def normalize(url):
    """
    Clean an url in order to add it to the servers list
    """
    url_info = urlparse(url)
    server = url_info.netloc
    uri = url_info.path
    while '//' in uri:
        uri = uri.replace('//', '/')
    url = 'http://%s%s' % (server, uri)
    if url[-1] != '/':
        url += '/'
    return url
    

def to_hex(byte_array):
    """
    String to hex
    """
    return ''.join(['%02X'%ord(byte) for byte in byte_array])
        
def from_hex(hexbytes):
    """
    Hex to string
    """
    return ''.join(['%c'%(int(hexbytes[index*2:(index+1)*2], 16))\
        for index in range(len(hexbytes)/2)])
        
def convert_bytes(size):
    """
    Python recipe from http://www.5dollarwhitebox.org/drupal/node/84
    """
    size = float(size)
    if size >= 1099511627776:
        terabytes = size / 1099511627776
        size = '%.2f TB' % terabytes
    elif size >= 1073741824:
        gigabytes = size / 1073741824
        size = '%.2f GB' % gigabytes
    elif size >= 1048576:
        megabytes = size / 1048576
        size = '%.2f MB' % megabytes
    elif size >= 1024:
        kilobytes = size / 1024
        size = '%.2f KB' % kilobytes
    else:
        size = '%.2f B' % size
    return size

def format_speed(speed):
    """
    Format speed text in bytes, Kb, Mb and Gb per sec.
    """
    if speed > 2**30:
        return '%0.2f Gb/s' % (float(speed)/2**30)
    elif speed > 2**20:
        return '%0.2f Mb/s' % (float(speed)/2**20)
    elif speed > 2**10:
        return '%0.2f Kb/s' % (float(speed)/2**10)
    else:
        return '%d b/s' % speed
