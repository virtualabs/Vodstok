
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
    def __init__(self):
        Exception.__init__(self)