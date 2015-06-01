#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file is part of mailpy - the mail API framework.
"""

import logging
import sys
import re

from mailpy.utils import parse_message
from mailpy.view import MailView

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s]: %(message)s'))
root_logger.addHandler(handler)
logger = root_logger.getChild('mail.py')


def main():
    sender, recipient, nexthop = sys.argv[1:]

    if nexthop == '_invalid_':
        raise SystemExit('Invalid resource "%s" from "%s"' % (recipient, sender))

    try:
        request = parse_message(sys.stdin, sender, recipient)
    except Exception as e:
        raise SystemExit('Could not parse message from "%s" sent to "%s". Error was: %s' % (sender, recipient, e))

    try:
        modname = request.resource
        viewname = modname.split('.')[-1]
        clsname = viewname[0].upper() + re.sub(r'_+([a-zA-Z0-9])', lambda m: m.group(1).upper(), viewname[1:])
        module = __import__(modname, fromlist=[clsname])
        viewcls = getattr(module, clsname)

        if not issubclass(viewcls, MailView):
            raise SystemExit('Mail view "%s" is not an instance of MailView' % viewcls.__name__)

        viewobj = viewcls()
    except Exception as exc:
        logger.exception(exc)
        raise SystemExit('Could not load view class from "%s": %s' % (request.resource, exc))

    logger.info('Processing mail request: %r', request)
    logger.debug('\twith content: %s', request)
    response = viewobj.router.dispatch_request(request)

    logger.info('Sending mail response: %r', response)
    logger.debug('\twith content: %s', response)
    response.send()  # Send mail via localhost:25


if __name__ == '__main__':
    main()
