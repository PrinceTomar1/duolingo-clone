"""Domain errors raised by the service layer.

Services know nothing about HTTP -- they raise these, and a single exception
handler in ``main.py`` maps each one to a status code. That keeps status-code
policy in one place and lets the same services be reused from the seed script
or a future worker without dragging FastAPI along.
"""


class DomainError(Exception):
    """Base class for every expected, caller-fixable failure."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """A referenced row does not exist."""

    status_code = 404


class ConflictError(DomainError):
    """The request contradicts the current state, e.g. finishing a finished attempt."""

    status_code = 409


class UnauthorizedError(DomainError):
    """A password-protected learner was named with the wrong password, or none."""

    status_code = 401


class SkillLockedError(DomainError):
    """The learner has not unlocked the skill this lesson belongs to."""

    status_code = 403


class OutOfHeartsError(DomainError):
    """The learner has no hearts left and cannot start or continue a lesson."""

    status_code = 403
