#!/usr/bin/env python2.7

import random
import string
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from multiprocessing.pool import ThreadPool
from quemail import QueMail, Email

import settings

def randString(length):
	return ''.join(random.SystemRandom().choice(string.letters + string.digits) for x in range(length))

def sendEmail(toaddr, subject, body):
	fromaddr = settings.EMAILUSER

	qm = QueMail.get_instance()
	qm.send(Email(subject=subject, text=body, adr_to=toaddr, adr_from=fromaddr, mime_type='html'))
