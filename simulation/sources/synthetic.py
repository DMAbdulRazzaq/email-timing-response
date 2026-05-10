import random
import numpy as np
import pandas as pd

from data.email_data import Email, SENDER_POOLS, SUBJECT_POOLS, PRIORITY_MAP
from simulation.sources.base import EmailSource


class SyntheticEmailSource(EmailSource):

    _LEVELS = ["high", "medium", "low"]
    _WEIGHTS = [0.20, 0.40, 0.40]  # mirrors real-world inbox distribution

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def get_email(self) -> Email:
        level = np.random.choice(self._LEVELS, p=self._WEIGHTS)
        p = PRIORITY_MAP[level]
        return Email(
            subject=random.choice(SUBJECT_POOLS[level]),
            sender=random.choice(SENDER_POOLS[level]),
            priority=p,
            sender_importance=p,
            waiting_time=random.randint(0, 60),
            workload=random.randint(1, 3),
            time_of_day=random.randint(0, 23),
        )

    def generate_batch(self, n: int = 100) -> pd.DataFrame:
        return pd.DataFrame([vars(self.get_email()) for _ in range(n)])
