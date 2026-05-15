import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "token.pkl"


def get_credentials_file():
    credentials_file = BASE_DIR / "credentials.json"

    if credentials_file.exists():
        return credentials_file

    client_secret_files = list(BASE_DIR.glob("client_secret*.json"))
    if client_secret_files:
        return client_secret_files[0]

    raise FileNotFoundError(
        "No Gmail OAuth credentials found. Add credentials.json or a "
        "client_secret*.json file to the project directory."
    )


def gmail_authenticate():
    creds = None

    # Load existing token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Authenticate if no valid token
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(get_credentials_file(), SCOPES)

            try:
                creds = flow.run_local_server(
                    port=8080,
                    open_browser=True,
                    authorization_prompt_message=(
                        "A browser window should open for Gmail authorization.\n"
                        "If it does not, copy this URL into your browser:\n{url}\n"
                    ),
                    success_message=(
                        "Gmail authorization complete. You can close this tab "
                        "and return to the terminal."
                    ),
                )
            except KeyboardInterrupt as exc:
                raise RuntimeError(
                    "Gmail authorization was cancelled. Run `python test_gmail.py` "
                    "again and complete the Google sign-in page before pressing "
                    "Ctrl+C."
                ) from exc

        # Save token
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)

    return service
