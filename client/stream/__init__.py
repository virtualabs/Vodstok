"""
Vodstok stream module
"""

from stream.filestream import FileStream, FileStreamIOError, \
    FileStreamEOF,MemoryStream

__all__ = [
	'MemoryStream',
	'FileStream',
	'FileStreamIOError',
	'FileStreamEOF'
]