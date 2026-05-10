from datetime import datetime


class Logger:

    def __init__(self, log_every: int = 100):
        self.log_every = log_every

    def episode(self, ep: int, reward: float, epsilon: float, q_size: int) -> None:
        if ep % self.log_every == 0:
            ts = datetime.now().strftime("%H:%M:%S")
            print(
                f"[{ts}] Episode {ep:>5} | Reward: {reward:>+7.1f} | "
                f"Epsilon: {epsilon:.3f} | Buffer/States: {q_size}"
            )

    def section(self, title: str) -> None:
        print(f"\n{'-'*55}")
        print(f"  {title}")
        print(f"{'-'*55}")

    def done(self, message: str) -> None:
        print(f"\n[DONE] {message}")
