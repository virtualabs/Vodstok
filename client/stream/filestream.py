"""
Vodstok file streams

Streams are commonly used in Vodstok to read and write data,
especially data coming from encrypted chunks. These streams
allow multipart upload and download with completely transparent
encryption.

"""

from os import urandom, SEEK_SET, SEEK_END
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from core.settings import Settings
from StringIO import StringIO
from hashlib import sha512



def pad(data):
    """
    Add PKCS7 padding to data
    """
    length = Settings.block_size - (len(data)%Settings.block_size)
    for i in range(length):
        data += chr(length)
    return data

def unpad(data):
    """
    Remove PKCS7 padding
    """
    length = ord(data[-1])
    return data[:-length]


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
        self.filename = None
        self.mode = None
        self.handle = fileobj
        if key is None:
            self.key = urandom(16)
        else:
            self.key = key
        self.iv = sha512(self.key).digest()[:16]
        self.__eof = False

    def eof(self):
        """
        Check if EOF
        """
        return self.__eof

    def get_key(self):
        """
        Retrieve the generated AES key
        """
        return self.key

    def get_key_hex(self):
        """
        Retrieve the generated AES key as hex
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

    def get_nb_chunks(self):
        """
        Retrieve file chunks number
        """
        size = self.size()
        nchunks = size/Settings.chunk_size
        if nchunks*Settings.chunk_size < size:
            nchunks += 1
        return nchunks

    def open(self):
        """
        Open file
        """
        try:
            self.handle = open(self.filename, self.mode)
        except IOError:
            raise FileStreamIOError()

    def encrypt_chunk(self, chunk):
        """
        Encrypt chunk
        """
        chunk_padded = pad(chunk)
        enc = AES.new(self.key, AES.MODE_CBC, self.iv)
        return b64encode(enc.encrypt(chunk_padded))

    def decrypt_chunk(self, enc_chunk):
        """
        Decrypt chunk
        """
        dec = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(dec.decrypt(b64decode(enc_chunk)))

    def read_chunk(self, index=None):
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
                return self.encrypt_chunk(chunk)
            except IOError:
                raise FileStreamIOError()
        else:
            raise FileStreamEOF()

    def write_chunk(self, content, index=None):
        """
        Write chunk to file. If index is given, write the index-th chunk to file.
        """
        # if id is provided then write chunk to file at the corresponding offset
        if index is not None:
            #print 'step to %d' % index
            offset = index*Settings.chunk_size
            self.handle.seek(offset, SEEK_SET)
		
        # decrypt chunk
        decrypted_chunk = self.decrypt_chunk(content)
        try:
            self.handle.write(decrypted_chunk)
        except IOError:
            raise FileStreamIOError()

    def close(self):
        """
        Close file
        """
        if self.handle is not None:
            self.handle.close()

class MemoryStream(FileStream):
    
    """
    Memory streams are the same as file streams, but only works in pure
    memory (no file created).
    
    This kind of stream is used by vodstok core to handle metadata storage
    over multiple chunks.
    """
    
    def __init__(self, memory_block, key=None):
        FileStream.__init__(self, StringIO(memory_block), key)

    def read(self):
        """
        Read the entire stream.
        
        This method returns the stream's content
        """
        self.handle.seek(0, SEEK_SET)
        return self.handle.getvalue()
