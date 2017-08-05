#!/usr/bin/env python3

import random
import string
from quemail import QueMail, Email

import settings

def randString(length):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for x in range(length))

def sendEmail(toaddr, subject, body):
    fromaddr = settings.EMAILFROM

    qm = QueMail.get_instance()
    qm.send(Email(subject=subject, text=body, adr_to=toaddr, adr_from=fromaddr, mime_type='html'))

def getScore(score, numplayers, rank):
    umas = {4:[15,5,-5,-15],
            5:[15,5,0,-5,-15]}
    return score / 1000.0 - 25 + umas[numplayers][rank - 1]

quarterSuffixes = {'1': 'st', '2': 'nd', '3': 'rd', '4': 'th'}

def parseQuarter(qstring):
    if not isinstance(qstring, str) or len(qstring) != 8:
        return None
    if not qstring[0:4].isdigit() or not qstring[5] in quarterSuffixes:
        return None
    return (int(qstring[0:4]), int(qstring[5]))

def formatQuarter(qtuple):
    return "{0} {1}{2}".format(qtuple[0], qtuple[1], 
                               quarterSuffixes[str(qtuple[1])])

def nextQuarter(qtuple):
    return (qtuple[0] + 1, 1) if qtuple[1] == 4 else (qtuple[0], qtuple[1] + 1)

def prevQuarter(qtuple):
    return (qtuple[0] - 1, 4) if qtuple[1] == 1 else (qtuple[0], qtuple[1] - 1)
