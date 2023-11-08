import audiobookdl.sources as sources
from .logging import print_error_file, error
from typing import Optional

class AudiobookDLException(Exception):
    error_description = "unknown"

    def __init__(self, error_description = None, **kwargs) -> None:
        if error_description:
            self.error_description = error_description
        self.data = kwargs

    def print(self) -> None:
        print_error_file(self.error_description, **self.data)

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

    def print(self):
        source_name_list = "\n".join([f" • {name}" for name in sources.get_source_names()])
        print_error_file(self.error_description, sources=source_name_list, **self.data)

class RequestError(AudiobookDLException):
    error_description = "request_error"

class UserNotAuthorized(AudiobookDLException):
    error_description = "user_not_authorized"

class MissingBookAccess(AudiobookDLException):
    error_description = "book_access"

class ConfigNotFound(AudiobookDLException):
    error_description = "config_not_found"
