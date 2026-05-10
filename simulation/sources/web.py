from data.email_data import Email
from simulation.sources.base import EmailSource


class WebEmailSource(EmailSource):
    """
    Receives one email submitted via the Flask web UI.
    Flask parses the POST body and passes a dict here.
    This class is only responsible for converting that dict → Email.
    The Flask routes live in ui/web_ui.py (UI responsibility stays separate).
    """

    def get_email(self, form_data: dict = None) -> Email:
        if form_data is None:
            raise ValueError("WebEmailSource requires form_data dict from Flask POST.")
        return Email(
            subject=form_data["subject"],
            sender=form_data["sender"],
            priority=int(form_data["priority"]),
            sender_importance=int(form_data["sender_importance"]),
            waiting_time=int(form_data["waiting_time"]),
            workload=int(form_data["workload"]),
            time_of_day=int(form_data["time_of_day"]),
        )
