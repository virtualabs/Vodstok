"""

Vodstok settings

chunk_size : upload/download chunk size
block_size : multiple of 16 (AES)
max_threads: number of threads to use for upload/download

"""
from core.helpers import VersionStr

class Settings:
    """
    Vodstok global settings
    """

    chunk_size = 32*1024 - 16
    block_size = 16
    max_threads = 5
    version = VersionStr('1.2.4')

    def __init__(self):
        pass

