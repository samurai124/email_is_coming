import mimetypes
import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from config import Config

class EmailSender:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.sender_email = Config.SENDER_EMAIL
        self.sender_password = Config.SENDER_PASSWORD
        self.sender_name = Config.SENDER_NAME

    def test_connection(self) -> tuple[bool, str]:
        """
        Tests SMTP server connection and credentials.
        Returns: (success: bool, message: str)
        """
        if not self.sender_email or not self.sender_password:
            return False, "SENDER_EMAIL or SENDER_PASSWORD is not configured in .env"

        try:
            context = ssl.create_default_context()
            if self.smtp_port == 465:
                # SSL Direct
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=15) as server:
                    server.login(self.sender_email, self.sender_password)
            else:
                # STARTTLS (default port 587)
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(self.sender_email, self.sender_password)

            return True, f"Successfully authenticated with {self.smtp_server} as {self.sender_email}"
        except smtplib.SMTPAuthenticationError as e:
            return False, (
                f"Authentication failed ({e.smtp_code}): {e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else str(e)}.\n"
                "Tip for Gmail: Ensure 2-Step Verification is ON and you are using a 16-character 'App Password', not your normal Google password."
            )
        except Exception as e:
            return False, f"Connection failed to {self.smtp_server}:{self.smtp_port} -> {str(e)}"

    def build_message(self, to_email: str, subject: str, body_text: str, resume_path: Path) -> MIMEMultipart:
        """
        Constructs a MIME multipart email message with headers, body, and resume attachment.
        """
        msg = MIMEMultipart()
        # Sender display name format: "John Doe <johndoe@example.com>"
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = self.sender_email

        # Attach text body
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        # Attach resume if it exists
        if resume_path and resume_path.exists():
            mime_type, _ = mimetypes.guess_type(str(resume_path))
            if mime_type is None:
                mime_type = "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)

            with open(resume_path, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            # Friendly attachment filename (e.g. "John_Doe_Resume.pdf")
            safe_name = "".join(c for c in self.sender_name if c.isalnum() or c in (" ", "_")).replace(" ", "_")
            out_filename = f"{safe_name}_Resume{resume_path.suffix}" if safe_name else resume_path.name
            
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{out_filename}"'
            )
            msg.attach(part)
        else:
            raise FileNotFoundError(f"Resume file not found at: {resume_path}")

        return msg

    def send_message(self, msg: MIMEMultipart) -> tuple[bool, str]:
        """
        Transmits the email via SMTP.
        Returns: (success: bool, message: str)
        """
        context = ssl.create_default_context()
        try:
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=25) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=25) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)
