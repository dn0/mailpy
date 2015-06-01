# -*- coding: utf-8 -*-
from mailpy.contrib.pelican.view import PelicanMailView
from mailpy.contrib.pelican.content import RstArticle


class BlogAdmin(PelicanMailView):
    """
    Pelican blog admin example with 3 methods: get, post, delete.
    """
    sender_required = ('user@example.com',)  # Implicit @sender_required for all MailView methods
    settings_file = '/var/www/blog/pelicanconf.py'  # Path to pelican settings file
    article_class = RstArticle  # Subclass of PelicanArticle used for new articles (rst file format is the default one)
    article_file_name = '%Y-%m-%d-{slug}'  # Without extension; valid placeholders: {slug} and strftime() directives
    # papi_settings = (  # PelicanAPI settings
    #     ('images_dir', 'images'),  # Directory inside content path used for storing attached images
    #     ('files_dir', 'files'),    # Directory inside content path used for storing non-image mail attachments
    #     ('repo_path', '/var/www/blog'),  # Set to enable automatic git commits after post() and delete()
    # )
