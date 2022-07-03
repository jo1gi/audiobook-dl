from .messages import print_error

class AudiobookDLException(Exception):
    error_description = "unknown"

    def __init__(self, **kwargs):
        self.data = kwargs


    def print(self):
        print_error(self.error_description, **self.data)

class DataNotPresent(AudiobookDLException):
    error_description = "data_not_present"

class FailedCombining(AudiobookDLException):
    error_description = "failed_combining"

class MissingCookies(AudiobookDLException):
    error_description = "missing_cookies"

class MissingDependency(AudiobookDLException):
    error_description = "missing_dependency"

class NoFilesFound(AudiobookDLException):
    error_description = "no_files_found"

class NoSourceFound(AudiobookDLException):
    error_description = "no_source_found"

class RequestError(AudiobookDLException):
    error_description = "request_error"

class UserNotAuthorized(AudiobookDLException):
    error_description = "user_not_authorized"
