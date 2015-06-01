#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file is part of mailpy - the mail API framework.
"""

import sys

from mailpy.utils import parse_message
from mailpy.contrib.examples.hello_world import TestView


def main():
    sender, recipient = sys.argv[1:]

    try:
        request = parse_message(sys.stdin, sender, recipient)
    except Exception as e:
        raise SystemExit('Could not parse message from "%s" sent to "%s". Error was: %s' % (sender, recipient, e))

    mail_view = TestView()
    response = mail_view.router.dispatch_request(request)
    # response.send()  # Send mail via localhost:25
    print(response)


if __name__ == '__main__':
    main()
