"""

Vodstok Exceptions

"""

class IncorrectParameterError(Exception):
    """
    Incorrect parameter error
    """
    def __init__(self):
        Exception.__init__(self)

class ServerIOError(Exception):
    """
    Server input/output error
    """
    def __init__(self):
        Exception.__init__(self)

class IncorrectFormatError(Exception):
    """
    Incorrect format error
    """
    def __init__(self):
        Exception.__init__(self)

class StorageException(Exception):
    """
    Storage related error
    """
    def __init__(self):
        Exception.__init__(self)

class VersionError(Exception):
    """
    Incompatible version error
    """
    def __init__(self):
        Exception.__init__(self)

