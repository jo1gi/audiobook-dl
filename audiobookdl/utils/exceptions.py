from .messages import print_error

class AudiobookDLException(Exception):
    error_description = "unknown"

    def __init__(self, **kwargs):
        self.data = kwargs


    def print(self):
        print_error(self.error_description, **self.data)

class UserNotAuthenticated(AudiobookDLException):
    error_description = "missing_cookies"

class NoFilesFound(AudiobookDLException):
    error_description = "no_files_found"

class NoSourceFound(AudiobookDLException):
    error_description = "no_source_found"

class MissingDependency(AudiobookDLException):
    error_description = "missing_dependency"

class FailedCombining(AudiobookDLException):
    error_description = "failed_combining"
