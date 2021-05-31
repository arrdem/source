"""
Ratchet - a 'ratcheting' messaging, queueuing and RPC system.
"""

from abc import ABC, abstractmethod


class Message:
    """Messages can be sent. That's it.

    Messages have headers, which may

    Other things can filter the stream of inbound messages and do log processing, but that's the whole basis of the
    thing.

    """


class Event:
    """Events may occur.

    An event is either pending, set, or timed out.

    # Messaging protocol

    The first message states that there IS an event, and provides a global ID by which the event may be referred to and
    a timeout. The initial state fo the event is `pending`.

    After the timeout has elapsed, the event MUST be DECLARED by any clients to have timed out. Attempts to set an event
    after it has timed out may be recorded, but MUST be ignored and MAY NOT alter the state of the event.

    A second message MAY be sent, DECLARING that the event has occurred. This transitions the state of the event from
    `pending` to `set`.

    Implementations MAY provide a message AFTER the timeout of an event occurred RECORDING that the event timed out
    without being set so that listening clients may rely on a shared central clock but this is not guranteed behavior
    and the timing need not be exact or transactional.

    """


class Request:
    """Requests may get a response.

    A request is either pending, responded, revoked or timed out.

    # Messaging protocol

    The first message states that there IS a request, provides a global ID by which the request may be referenced, a
    timeout for the request and a request body.

    After the timeout has elapsed, the request MUST be DECLARED by any clients to have timed out. Attempts to deliver a
    response to a request after it has timed out may be recorded, but MUST be ignored and MAY NOT alter the state of the
    request.

    A second message MAY be sent, RESPONDING to to the request. This transitions the state of the request from `pending`
    to `responded`.

    A second message MAY be sent, REVOKING the request. This transitions the state of the request from `pending` to
    `revoked`, and MAY cause any system processing requests either to skip this one or to cancel processing the request.
    Revocation of a `responded` or `timed out` request is ignored.

    """


class Driver(ABC):
    """Shared interface for Ratchet backend drivers."""

    @abstractmethod
    def __init__(message_ttl=60000, message_space="_", message_author=""):
        """Initialize the driver."""

    @abstractmethod
    def create_message(
        self, message: str, ttl: int = None, space: str = None, author: str = None
    ) -> Message:
        """Create a single message."""

    @abstractmethod
    def create_event(
        self, timeout: int, ttl: int = None, space: str = None, author: str = None
    ):
        """Create a (pending) event."""

    @abstractmethod
    def set_event(
        self, timeout: int, ttl: int = None, space: str = None, author: str = None
    ):
        """Attempt to mark an event as set."""

    @abstractmethod
    def create_request(
        self,
        body: str,
        timeout: int,
        ttl: int = None,
        space: str = None,
        author: str = None,
    ):
        """Create a (pending) request."""

    @abstractmethod
    def deliver_request(
        self,
        request_id,
        response: str,
        ttl: int = None,
        space: str = None,
        author: str = None,
    ):
        """Deliver a response to a (pending) request."""

    @abstractmethod
    def revoke_request(
        self, request_id, ttl: int = None, space: str = None, author: str = None
    ):
        """Revoke a (pending) request."""
