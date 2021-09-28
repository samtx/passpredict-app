class NotReachable(Exception):
    """Raised when a pass is not reachable on a time window"""


class PropagationError(Exception):
    """Raised when a calculation issue is found"""