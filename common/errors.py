class DesiApiException(Exception):
    pass

class DataNotFoundException(DesiApiException):
    pass

class MalformedRequestException(DesiApiException):
    pass

class ServerFailedException(DesiApiException):
    pass
