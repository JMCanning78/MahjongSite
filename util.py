#!/usr/bin/env python3

import random
import string
import operator
from quemail import QueMail, Email

import settings

def stringify(x):
    if x is None or isinstance(x, str):
        return x
    elif isinstance(x, bytes):
        return x.decode()
    else:
        return str(x)

def randString(length):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for x in range(length))

def sendEmail(toaddr, subject, body):
    fromaddr = settings.EMAILFROM

    qm = QueMail.get_instance()
    qm.send(Email(subject=subject, text=body, adr_to=toaddr, adr_from=fromaddr, mime_type='html'))

def prompt(msg, default=None):
    resp = None
    accepted_responses = ['y', 'Y', 'yes', 'Yes', 'n', 'N', 'no', 'No']
    guide = "[y/n]"
    if default and default in accepted_responses:
        accepted_responses.append('')
        guide = "[Y/n]" if default.lower().startswith('y') else "[y/N]"
    while resp not in accepted_responses:
        resp = input("{0} {1}? ".format(msg, guide))
        if resp not in accepted_responses:
            print("Unrecognized response, '{0}'.\nPlease choose among {1}".
                  format(resp, accepted_responses))
    return (resp.lower().startswith('y') if len(resp) > 0 or default == None
            else default.lower().startswith('y'))

def identity(x):
    return x

def first(seq, elem, key=identity, not_found=ValueError,
          comparison=operator.__eq__):
    for i, e in enumerate(seq):
        if comparison(elem, key(e)):
            return i
    if isinstance(not_found, Exception):
        raise not_found('Cannot find {} in {}'.format(elem, seq))
    else:
        return not_found

