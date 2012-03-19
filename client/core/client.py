import re
import os
import urllib,httplib,urllib2
import urlparse

class VodstokStorage:
	
	"""
	Vodstok remote storage client
	"""	

	def __init__(self, url):
		url_info = urlparse.urlparse(url)
		self.server = url_info.netloc
		self.uri = url_info.path
		self.url = self.server+self.uri
		self.posturl = self.uri
		self.dlurl = 'http://%s%s?chunk=' % (self.server,self.uri)
		self.puburl = 'http://%s%s?register=' % (self.server,self.uri)
		self.statsurl = 'http://%s%s?stats' % (self.server,self.uri)
		self.epurl = 'http://%s%s?endpoints' % (self.server,self.uri)
		
	def upload(self, chunk):
		"""
		Upload of raw chunk of data
		"""
		params = {
			'chunk':chunk,
		}
		
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
				return None
		else:
			return None

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
				return None
		except urllib2.URLError,e:
			return None

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
                        return False

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
                        return []
	
	def capacity(self):
		"""
		Get endpoint statistics (quota, used space and number of chunks present)
		"""
		r = urllib2.Request(self.statsurl)
		resp = urllib2.urlopen(r)
		if resp:
			content = resp.read()
			r = re.search('quota:([0-9]+),used:([0-9]+),chunks:([0-9]+)', content)
			if r:
				return (int(r.group(1)),int(r.group(2)),int(r.group(3))) 
		else:
			return None
		

