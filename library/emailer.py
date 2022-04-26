# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, too-many-arguments, too-many-locals, too-few-public-methods, dangerous-default-value
"""Emailer"""
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.image import MIMEImage

from configparser import ConfigParser
from library.config_parser import config_section_parser

class Email():
    """Class for Email"""

    # # INITIALIZE
    # def __init__(self):
    #     """The Constructor Email class"""
    #     pass

    def send_email(self, send_to, message, subject, files=[], image=False):
        """Send Email"""
        # INIT CONFIG
        config = ConfigParser()
        # CONFIG FILE
        config.read("config/config.cfg")

        send_to = [send_to]

        # SET CONFIG VALUES
        email = config_section_parser(config, "EMAIL")['email']
        password = config_section_parser(config, "EMAIL")['password']

        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = ", ".join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject


        # msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(message, 'html'))

        if image:

            fip = open(image, 'rb')
            img = MIMEImage(fip.read())
            fip.close()
            img.add_header('Content-ID', '<{}>'.format(image))
            msg.attach(img)

        for fle in files or []:
            with open(fle, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=basename(fle)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(fle)
            msg.attach(part)

        # Gmail Login
        server = smtplib.SMTP('smtp.gmail.com:587')
        # server = smtplib.SMTP('smtp.office365.com:587')

        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(email, password)

        message = msg.as_string()

        server.sendmail(email, send_to, message)
        server.quit()

        return 1
