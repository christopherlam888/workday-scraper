import smtplib
from email.mime.text import MIMEText


def compose_email(jobs):
    body = """
    <html>
      <body>
    """
    for job_info in jobs:
        body += f"""
        <p><a href="{job_info['job_href']}">{job_info['company']}: {job_info['job_title']}</a></p>
        """
    body += """
      </body>
    </html>
    """
    return body


def send_email(subject, body, sender, recipients, password):
    # Create a MIMEText object with the body of the email.
    msg = MIMEText(body, "html")
    # Set the subject of the email.
    msg["Subject"] = subject
    # Set the sender's email.
    msg["From"] = sender
    # Join the list of recipients into a single string separated by commas.
    msg["To"] = ", ".join(recipients)

    # Connect to Gmail's SMTP server using SSL.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        # Login to the SMTP server using the sender's credentials.
        smtp_server.login(sender, password)
        # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
        smtp_server.sendmail(sender, recipients, msg.as_string())
    # Print a message to console after successfully sending the email.
    print("Message sent!")
