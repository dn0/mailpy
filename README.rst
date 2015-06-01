mailpy
######

Mail API framework with support for `Pelican static site generator <http://getpelican.com/>`_.

Create and call RESTful API methods via SMTP (just by sending emails to the right email address).


Installation
------------

No pypi package for now::

    pip install https://github.com/dn0/mailpy/tarball/master


Usage
-----

Pipe messages into `mail.py <https://github.com/dn0/mailpy/tree/master/bin>`_::

    echo -e "From: <user@example.com>\nTo: <test@example.com>\n\n..." > msg

    cat msg | bin/mail.simple.py user@example.com test@example.com

    ...
    Hello World


See `examples <https://github.com/dn0/mailpy/tree/master/mailpy/contrib/examples>`_ or `wiki <https://github.com/dn0/mailpy/wiki>`_ for more info.


License
-------

`BSD 3-Clause License <https://github.com/dn0/mailpy/blob/master/LICENSE>`_

