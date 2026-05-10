import random

from data.email_data import Email
from data.enron_loader import EnronLoader, RawEmail
from simulation.sources.base import EmailSource
from simulation.sources.nlp_extractor import NLPEmailExtractor


class EnronEmailSource(EmailSource):
    """
    EmailSource backed by real Enron emails.
    Cycles through the loaded dataset infinitely —
    each call to get_email() returns a real email with
    features inferred by NLPEmailExtractor.

    WHY THIS MATTERS:
        The agent trains on 500k real email patterns —
        real urgency signals, real sender domains, real subjects.
        This is what makes the trained model actually generalize.
    """

    def __init__(self, dataset_path: str, max_emails: int = 50_000):
        loader = EnronLoader(dataset_path, max_emails)
        self._emails = loader.load()
        self._extractor = NLPEmailExtractor()
        self._index = 0
        random.shuffle(self._emails)

    def get_email(self) -> Email:
        raw = self._emails[self._index % len(self._emails)]
        self._index += 1
        return self._extractor.extract(raw.subject, raw.sender)

    def __len__(self) -> int:
        return len(self._emails)


# Backward compatibility alias
EnronSource = EnronEmailSource
