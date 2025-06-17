import email

from imapclient import IMAPClient

HOST = 'mail.ecloud.global'
USERNAME = 'mantis.flow@e.email'
PASSWORD = 'Q3otNRm3sLxd'

imported_message = []

with IMAPClient(HOST) as server:
    server.login(USERNAME, PASSWORD)
    server.select_folder("INBOX", readonly=True)

    messages = server.search("UNSEEN")
    for uid, message_data in server.fetch(messages, "RFC822").items():
        email_message = email.message_from_bytes(message_data[b"RFC822"])
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            body = part.get_payload(decode=True)

            if content_type == "text/plain" and "attachment" not in content_disposition:

                imported_message.append({"UID": uid, "From": email_message.get("From"),
                                         "Subject": email_message.get("Subject"),
                                         "Message": body})

