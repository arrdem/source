"""
An abstract or base Flowmetal DB.
"""

from abc import (
    abstractclassmethod,
    abstractmethod,
)


class Db(ABC):
    """An abstract Flowmetal DB."""

    @abstractclassmethod
    def connect(cls, config):
        """Build and return a connected DB."""

    @abstractmethod
    def disconnect(self):
        """Disconnect from the underlying DB."""

    def close(self):
        """An alias for disconnect allowing for it to quack as a closable."""
        self.disconnect()

    @abstractmethod
    def reconnect(self):
        """Attempt to reconnect; either after an error or disconnecting."""
