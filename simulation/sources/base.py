from abc import ABC, abstractmethod
from data.email_data import Email


class EmailSource(ABC):

    @abstractmethod
    def get_email(self) -> Email:
        """Return one Email instance from any source."""
        pass
