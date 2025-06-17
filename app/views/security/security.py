from flask_security import MailUtil
from flask_mailing import Message
from app.common import mail
from app.common.common_utils import run_async_in_thread


class MyMailUtil(MailUtil):
    """ Override Flask-Security-Too default of Flask-Mail
        to send an email via the Flask-Mailing extension.
        Using Flask 2.0+ async to send asynchronously
    """

    def send_mail(
        self,
        template: str,
        subject: str,
        recipient: str,
        sender: str | tuple,
        body: str,
        html: str | None,  # Allow html to be None
        **kwargs: str
    ) -> None:
        """ Override Flask-Security-Too defaults for mail send using flask-mailing

        :param template: the Template name. The message has already been rendered
            however this might be useful to differentiate why the email is being sent.
        :param subject: Email subject
        :param recipient: Email recipient
        :param sender: who to send email as (see :py:data:`SECURITY_EMAIL_SENDER`)
        :param body: the rendered body (text)
        :param html: the rendered body (html)
        """
        # Call the external send_email function to send the email
        message = Message(
            subject=subject,
            recipients=[recipient],
            body=html,
            subtype="html"
        )
        run_async_in_thread(
            mail.send_message(message)
        )

