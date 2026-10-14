"""Domain errors raised by service functions.

Views translate these into friendly form/message responses; they never expose
internal state or private data. Permission failures use Django's PermissionDenied
so they map to HTTP 403.
"""


class SafeRideError(Exception):
    """Base class for expected, user-facing business rule failures."""

    default_message = "This action could not be completed."

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


class EligibilityError(SafeRideError):
    default_message = "Your account is not eligible for this action."


class StateError(SafeRideError):
    default_message = "This action is not allowed in the current state."


class CapacityError(SafeRideError):
    default_message = "This bus is full."


class DuplicateError(SafeRideError):
    default_message = "You already have an active request for this trip."


class ExpiredError(SafeRideError):
    default_message = "This reservation has expired."


class CodeError(SafeRideError):
    default_message = "The boarding code is not valid."
