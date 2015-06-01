# -*- coding: utf-8 -*-
from .router import router
from .exceptions import MailViewError

__all__ = ('MailView',)


class MailView(object):
    """
    Base class for class-based mail views.

    Every public method will be a mail view accepting one request parameter.
    """
    _debug = True
    _auto_registration = True
    _decorators_cache = None
    sender_required = None

    def __init__(self):
        """Register mail view and mail methods"""
        self.router = router.register_view(__name__)
        self._register_methods()

    def _register_methods(self):
        """Register mail methods from this view"""
        for name in dir(self):
            if not name.startswith('_'):
                attr = getattr(self, name)

                if attr and hasattr(attr, '__call__'):
                    method_name = getattr(attr, 'mail_method', None)

                    if method_name is False:
                        continue

                    if method_name or self._auto_registration:
                        self.router.register_method(attr, name=method_name or name)

    def _check_sender(self, request, view_fun):
        """Check sender requirements"""
        sender = request.sender

        if not getattr(view_fun, 'sender_required_ignore_global', False):
            if self.sender_required is not None and sender not in self.sender_required:
                return False

        sender_required = getattr(view_fun, 'sender_required', None)

        if sender_required is None:
            return True

        return sender in sender_required

    def _process_view(self, request, view_fun):
        """Perform checks and run the mail view method"""
        if not self._check_sender(request, view_fun):
            raise MailViewError(request, 'Forbidden', status_code=403)

        return view_fun(request)
