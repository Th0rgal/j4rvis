import smtplib
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

        # Create the MIME object
        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

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
