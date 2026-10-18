"""Service layer errors rendered with the module JSON error convention."""


class ApiError(Exception):
    """A capability call that failed for a stated reason."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class BadInput(ApiError):
    def __init__(self, message):
        super().__init__(400, message)


class NotFound(ApiError):
    def __init__(self, message):
        super().__init__(404, message)


class Conflict(ApiError):
    def __init__(self, message):
        super().__init__(409, message)
