import re
import os
import urllib,httplib,urllib2
import urlparse
from base64 import b64encode,b64decode


class ServerIOError(Exception):
	def __init__(self):
		Exception.__init__(self)

class Server:	
	"""
	Vodstok remote storage client
	"""	
	
	def __init__(self, url):
		url_info = urlparse.urlparse(url)
		self.scheme = url_info.scheme		
		self.server = url_info.netloc
		self.uri = url_info.path
		self.url = urlparse.urlunparse((self.scheme,self.server,self.uri,'','',''))
		self.posturl = self.uri
		self.dlurl = '%s://%s%s?chunk=' % (self.scheme,self.server,self.uri)
		self.puburl = '%s://%s%s?register=' % (self.scheme,self.server,self.uri)
		self.statsurl = '%s://%s%s?stats' % (self.scheme,self.server,self.uri)
		self.epurl = '%s://%s%s?endpoints' % (self.scheme,self.server,self.uri)
		
	def upload(self, chunk):
		"""
		Upload of raw chunk of datae
		"""
		params = {
			'chunk':chunk,
		}
		try:
			# Send request
			p = urllib.urlencode(params)
			r = httplib.HTTPConnection(self.server)
			r.putrequest('POST',self.posturl)
			r.putheader('Content-Type','application/x-www-form-urlencoded')
			r.putheader('Content-Length',str(len(p)))
			r.endheaders()
			r.send(p)
			
			# Analyze response		
			resp = r.getresponse()
			if resp.status == 200:
				# check if the returned ID is a MD5 hash
				id = resp.read()
				if re.match('[0-9a-fA-F]{32}',id):
					return id
				else:
					raise ServerIOError()
			else:
				raise ServerIOError()
		except:
			raise ServerIOError()
			
	def download(self, id):
		"""
		Download a chunk of data based on its ID (returned by the upload method above)
		"""
		try:
			r = urllib2.Request(self.dlurl+id)
			resp = urllib2.urlopen(r)
			if resp:
				return resp.read()
			else:
				raise ServerIOError()
		except urllib2.URLError,e:
			raise ServerIOError()
	
	def publish(self, endpoint_url):
		"""
		Publish a given endpoint on this endpoint
		"""
		try:
		        r = urllib2.Request(self.puburl+urllib.quote(endpoint_url))
		        resp =  urllib2.urlopen(r)
		        if resp:
		                return (resp.getcode() == 200)
		        return False
		except urllib2.HTTPError,e:
		        if e.getcode == 404:
		                return False
		        raise ServerIOError()
	
	def listRegisteredEndpoints(self):
	    """
	    Retrieve a sample of published endpoints
	    """
	    try:
	            r = urllib2.Request(self.epurl)
	            resp =  urllib2.urlopen(r)
	            if resp:
	                    return resp.read().split(',')
	            return []
	    except urllib2.HTTPError,e:
	            raise ServerIOError()
	
	def alias(self, a):
		return '%s#%s'%(self.url,a)

	def check(self):
		try:
			data = b64encode(os.urandom(16))
			chunk_id = self.upload(data)
			output = self.download(chunk_id)
			return output==data
		except ServerIOError:
			return False		


	def capacity(self):
		"""
		Get endpoint statistics (quota, used space and number of chunks present)
		"""
		try:
			r = urllib2.Request(self.statsurl)
			resp = urllib2.urlopen(r)
			if resp:
				content = resp.read()
				r = re.search('quota:([0-9]+),used:([0-9]+),chunks:([0-9]+)', content)
				if r:
					return (int(r.group(1)),int(r.group(2)),int(r.group(3))) 
			else:
				return None
		except urllib2.HTTPError:
			return None
		except httplib.InvalidURL:
			return None