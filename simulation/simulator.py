import os
import sys

from data.email_data import Email
from simulation.sources.base import EmailSource

# Add the project root to sys.path if run directly
# We use insert(0, ...) so that our local 'data' folder takes precedence
# over any globally installed 'data' package from pip.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class EmailSimulator:
    """
    Orchestrates email retrieval from any EmailSource.
    The RL environment will talk to this class only — never to a source directly.
    """

    def __init__(self, source: EmailSource):
        self._source = source

    def next_email(self) -> Email:
        return self._source.get_email()
