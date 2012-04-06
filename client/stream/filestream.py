from os import urandom,SEEK_SET,SEEK_END
from Crypto.Cipher import AES
from base64 import b64encode,b64decode
from core.settings import Settings
from random import shuffle
from StringIO import StringIO

class FileStreamIOError(Exception):
	"""
	FileStream IO Error exception
	"""
	def __init__(self):
		Exception.__init__(self)

class FileStreamEOF(Exception):
	"""
	FileStream End Of File exception
	"""
	def __init__(self):
		Exception.__init__(self)

class FileStream:
	"""
	FileStream class
	
	Allows random access read/write operations on file, with
	inline chunk encryption and decryption.
	"""
	def __init__(self, fileobj, key=None):
		self.handle = fileobj
		if key is None:
			self.key = urandom(16)
		else:
			self.key = key
		self.__eof = False

	def __pad(self, data):
		"""
		Add PKCS7 padding to data
		"""
		l = Settings.block_size - (len(data)%Settings.block_size)
		for i in range(l):
			data += chr(l)
		return data
		
	def __unpad(self, data):
		"""
		Remove PKCS7 padding
		"""
		l = ord(data[-1])
		return data[:-l]

	def eof(self):
		"""
		Check if EOF
		"""
		return self.__eof

	def getKey(self):
		"""
		Retrieve the generated AES key
		"""
		return self.key
		
	def getKeyHex(self):
		"""
		Retrive the generated AES key as hex
		"""
		return self.key.encode('hex')

	def size(self):
		"""
		Retrieve file size
		"""
		cur = self.handle.tell()
		self.handle.seek(0, SEEK_END)
		size = self.handle.tell()
		self.handle.seek(cur, SEEK_SET)
		return size
		
	def getNbChunks(self):
		"""
		Retrieve file chunks number
		"""
		size = self.size()
		nchunks = size/Settings.chunk_size
		if nchunks*Settings.chunk_size<size:
			nchunks+=1
		return nchunks

	def open(self):
		"""
		Open file
		"""
		try:
			self.handle = open(self.filename, self.mode)
		except IOError,e:
			raise FileStreamIOError()

	def encryptChunk(self, chunk):
		"""
		Encrypt chunk
		"""
		chunk_padded = self.__pad(chunk)
		enc = AES.new(self.key, AES.MODE_CBC)
		return b64encode(enc.encrypt(chunk_padded))
		
	def decryptChunk(self, enc_chunk):
		"""
		Decrypt chunk
		"""
		dec = AES.new(self.key, AES.MODE_CBC)
		return self.__unpad(dec.decrypt(b64decode(enc_chunk)))


	def readChunk(self, index=None):
		"""
		Read chunk. If index is given, read the given chunk
		"""
		# if id is provided then read chunk from file at the given offset
		if index is not None:
			self.__eof = False
			offset = index*Settings.chunk_size
			self.handle.seek(offset, SEEK_SET)		

		# read and encrypt chunk if not eof
		if not self.__eof:
			try:
				chunk = self.handle.read(Settings.chunk_size)
				if len(chunk)==0:
					raise FileStreamEOF()
				#elif len(chunk)<Settings.chunk_size:
				#	self.__eof = True
				return self.encryptChunk(chunk)
			except IOError,e:
				raise FileStreamIOError()
		else:
			raise FileStreamEOF()

	def writeChunk(self, bytes, index=None):
		"""
		Write chunk to file. If index is given, write the index-th chunk to file.
		"""
		# if id is provided then write chunk to file at the corresponding offset
		if index is not None:
			#print 'step to %d' % index
			offset = index*Settings.chunk_size
			self.handle.seek(offset, SEEK_SET)
		
		# decrypt chunk
		dec_chunk = self.decryptChunk(bytes)
		try:
			self.handle.write(dec_chunk)
		except IOError,e:
			raise FileStreamIOError()

	def close(self):
		"""
		Close file
		"""
		if self.handle is not None:
			self.handle.close()

class MemoryStream(FileStream):
	def __init__(self, buffer, key=None):
		FileStream.__init__(self, StringIO(buffer), key)

	def read(self):
		self.handle.seek(0, SEEK_SET)
		return self.handle.getvalue()

