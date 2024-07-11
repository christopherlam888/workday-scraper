import smtplib
from email.mime.text import MIMEText


def compose_email(jobs):
    body = """
    <html>
      <head>
        <style>
          body {font-family: Arial, sans-serif; margin: 20px;}
          h2 {color: #2e6c80;}
          table {width: 100%; border-collapse: collapse;}
          th, td {padding: 5px; text-align: left; border-bottom: 1px solid #ddd;}
          th {background-color: #f2f2f2;}
          tr:hover {background-color: #f5f5f5;}
          a {color: #1e90ff; text-decoration: none;}
        </style>
      </head>
      <body>
        <h2>Today's Job Postings</h2>
        <table>
          <tr>
            <th>Company</th>
            <th>Job Title</th>
            <th>Link</th>
          </tr>
    """
    for job_info in jobs:
        body += f"""
          <tr>
            <td>{job_info['company']}</td>
            <td>{job_info['job_title']}</td>
            <td><a href="{job_info['job_href']}">View Job Posting</a></td>
          </tr>
        """
    body += """
        </table>
        <p>APPLY SOONER THAN LATER</p>
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
