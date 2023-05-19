import smtplib
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .parsers import parse_input


def send_email_builder(email, password, server_url, port):
    def send_email(txt) -> str:
        # Email details
        data = parse_input(txt)
        to_email = data["to_email"]
        subject = data["subject"]
        body = data["body"]
        files = data["files"]

        # Create the MIME object
        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        for path in files:
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", "attachment; filename={}".format(Path(path).name)
            )
            msg.attach(part)

        # Send the email
        try:
            with smtplib.SMTP_SSL(server_url, port) as server:
                server.login(email, password)
                text = msg.as_string()
                server.sendmail(email, to_email, text)
                return "Email sent successfully."
        except Exception as e:
            return f"Error occurred while sending the email: {e}"

    return send_email
