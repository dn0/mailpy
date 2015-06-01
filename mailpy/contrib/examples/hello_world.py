# -*- coding: utf-8 -*-
from mailpy.view import MailView
from mailpy.response import TextMailResponse
from mailpy.decorators import sender_required


class TestView(MailView):
    """
    Simple mail view with one method.
    """
    # noinspection PyMethodMayBeStatic
    @sender_required('user@example.com', 'user@example.net')
    def test(self, request):
        """You can call this method by sending an email to test@example.com"""
        return TextMailResponse(request, 'Hello World', charset='us-ascii')
