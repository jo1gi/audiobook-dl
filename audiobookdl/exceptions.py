import audiobookdl.sources as sources
from .logging import print_error_file, error
from typing import Optional

class AudiobookDLException(Exception):
    error_description = "unknown"

    def __init__(self, **kwargs):
        self.data = kwargs

    def print(self):
        print_error_file(self.error_description, **self.data)
        extra_data = self.extra_data()
        if extra_data:
            error(extra_data)


    def extra_data(self) -> Optional[str]:
        pass

class DataNotPresent(AudiobookDLException):
    error_description = "data_not_present"

class FailedCombining(AudiobookDLException):
    error_description = "failed_combining"

class MissingDependency(AudiobookDLException):
    error_description = "missing_dependency"

class NoFilesFound(AudiobookDLException):
    error_description = "no_files_found"

class NoSourceFound(AudiobookDLException):
    error_description = "no_source_found"

    def extra_data(self) -> Optional[str]:
        return "\n".join([f" • {name}" for name in sources.get_source_names()])

class RequestError(AudiobookDLException):
    error_description = "request_error"

class UserNotAuthorized(AudiobookDLException):
    error_description = "user_not_authorized"
    error_description = "user_not_authorized"
