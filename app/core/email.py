from typing import Dict, Any, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader
import os

# Email configuration
email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/email')
)

# Initialize FastMail
fastmail = FastMail(email_conf)

# Initialize Jinja2 environment
template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/email'))
)

async def send_email(
    email_to: str,
    subject: str,
    template_name: str,
    template_data: Dict[str, Any]
) -> None:
    """Send an email using a template."""
    # Render template
    template = template_env.get_template(template_name)
    html_content = template.render(**template_data)

    # Create message
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype="html"
    )

    # Send email
    await fastmail.send_message(message) 