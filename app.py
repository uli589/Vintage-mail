import imaplib
import email
import os
import time
import requests

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
WEBHOOK = os.getenv("WEBHOOK")

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")
CHECK_EVERY_SECONDS = int(os.getenv("CHECK_EVERY_SECONDS", "60"))

def send_to_discord(text: str):
    if not WEBHOOK:
        return
    requests.post(WEBHOOK, json={"content": text}, timeout=15)

def fetch_unseen_subjects():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select(IMAP_FOLDER)

    result, data = mail.search(None, "UNSEEN")
    if result != "OK":
        mail.logout()
        return []

    ids = data[0].split()
    subjects = []

    for num in ids[:10]:  # safety: max 10 pro check
        result, msg_data = mail.fetch(num, "(RFC822)")
        if result != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])

        subject = msg.get("subject", "(no subject)")
        from_ = msg.get("from", "")
        subjects.append((from_, subject))

        # als gelesen markieren, damit es nicht doppelt kommt
        mail.store(num, "+FLAGS", "\\Seen")

    mail.logout()
    return subjects

def main():
    send_to_discord("✅ Vintage-Mail-Monitor gestartet.")
    while True:
        try:
            if not EMAIL_USER or not EMAIL_PASS or not WEBHOOK:
                # Nur in Logs schreiben
                time.sleep(CHECK_EVERY_SECONDS)
                continue

            items = fetch_unseen_subjects()
            for from_, subject in items:
                send_to_discord(f"🆕 Neue Alert-Mail\nVon: {from_}\nBetreff: {subject}")

        except Exception as e:
            # Fehler nach Discord schicken (optional)
            send_to_discord(f"⚠️ Fehler im Monitor: {type(e).__name__}: {e}")

        time.sleep(CHECK_EVERY_SECONDS)

if __name__ == "__main__":
    main()
