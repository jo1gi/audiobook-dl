class CookiesNotLoadedException(Exception):
    pass

class UserNotAuthenticated(Exception):
    pass

class ServiceNotImplementedException(Exception):
    def __init__(self, fn, service):
        super().__init__(f"Function {fn} is not implemented for {service}")
