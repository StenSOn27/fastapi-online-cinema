import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

import aiosmtplib
from src.exceptions.emails import BaseEmailError
from src.notifications.interfaces import EmailSenderInterface


class EmailSender(EmailSenderInterface):

    def __init__(
        self,
        hostname: str,
        port: int,
        email: str,
        password: str,
        use_tls: bool,
        template_dir: str,
        activation_email_template_name: str,
        activation_email_complete_template_name: str
    ):
        self._hostname = hostname
        self._port = port
        self._email = email
        self._password = password
        self._use_tls = use_tls
        self._activation_email_template_name = activation_email_template_name
        self._activation_email_complete_template_name = activation_email_complete_template_name

        self._env = Environment(loader=FileSystemLoader(template_dir))

    async def _send_email(self, recipient: str, subject: str, html_content: str) -> None:
        message = MIMEMultipart()
        message["From"] = self._email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        try:
            smtp = aiosmtplib.SMTP(hostname=self._hostname, port=self._port, start_tls=self._use_tls)
            await smtp.connect()
            if self._use_tls:
                await smtp.starttls()
            await smtp.login(self._email, self._password)
            await smtp.sendmail(self._email, [recipient], message.as_string())
            await smtp.quit()
        except aiosmtplib.SMTPException as error:
            logging.error(f"Failed to send email to {recipient}: {error}")
            raise BaseEmailError(f"Failed to send email to {recipient}: {error}")

    async def send_activation_email(self, email: str, activation_link: str) -> None:
        template = self._env.get_template(self._activation_email_template_name)
        html_content = template.render(email=email, activation_link=activation_link)
        subject = "Account Activation"
        await self._send_email(email, subject, html_content)

    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        template = self._env.get_template(self._activation_email_complete_template_name)
        html_content = template.render(email=email, login_link=login_link)
        subject = "Account Activation"
        await self._send_email(email, subject, html_content)
