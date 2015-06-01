# -*- coding: utf-8 -*-
def mail_method(name=None, register=True):
    """
    Decorator used to explicitly register a mail view method.
    """
    def mail_method_decorator(fun, method_name=name):
        if register:
            if method_name is None:
                method_name = fun.__name__

            fun.mail_method = method_name
        else:
            fun.mail_method = False

        return fun

    if hasattr(name, '__call__'):
        return mail_method_decorator(name, method_name=None)
    else:
        return mail_method_decorator


def sender_required(*senders, **options):
    """
    Check request sender against a list of valid mail addresses.
    """
    def sender_required_decorator(fun):
        fun.sender_required_ignore_global = options.get('ignore_global', False)
        fun.sender_required = senders

        return fun

    return sender_required_decorator
