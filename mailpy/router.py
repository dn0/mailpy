# -*- coding: utf-8 -*-
from .response import MailResponse
from .exceptions import MailViewAlreadyRegistered, MailMethodAlreadyRegistered, MailError, MailViewError


class MailViewRouter(dict):
    """
    Map mail method names to mail view functions.
    """
    # noinspection PyMissingConstructor
    def __init__(self, resource):
        self.resource = resource

    # noinspection PyMethodOverriding
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.resource)

    def register_method(self, fun, name=None):
        """Register mail view method"""
        if name is None:
            name = fun.__name__

        if name in self:
            raise MailMethodAlreadyRegistered(name)

        self[name] = fun

    def dispatch_request(self, request):
        """Find and run the appropriate view method and return a MailResponse response object"""
        try:
            try:
                view_fun = self[request.method]
            except KeyError:
                raise MailViewError(request, 'Not Implemented', status_code=501)

            # noinspection PyProtectedMember
            response = view_fun.__self__._process_view(request, view_fun)

            if not isinstance(response, MailResponse):
                raise TypeError('Method %s at %s did not return a MailResponse object' % (request.method,
                                                                                          request.resource))
        except MailError as exc:
            response = exc
        except Exception as exc:
            errmsg = 'Internal Server Error: %s' % exc

            # noinspection PyUnboundLocalVariable,PyProtectedMember
            if view_fun.__self__._debug:
                import traceback
                errmsg += '\n\n%s' % traceback.format_exc()

            response = MailViewError(request, errmsg, status_code=500)

        return response


class MailRouter(dict):
    """
    Map mail resource names to mail view objects.
    """
    def __setitem__(self, key, value):
        assert isinstance(value, MailViewRouter), 'value must be an instance of %s' % MailViewRouter
        return super(MailRouter, self).__setitem__(key, value)

    def register_view(self, resource):
        """Register mail view object"""
        if resource in self:
            raise MailViewAlreadyRegistered(resource)

        self[resource] = MailViewRouter(resource)

        return self[resource]


router = MailRouter()
