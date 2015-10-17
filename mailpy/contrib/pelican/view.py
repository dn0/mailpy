# -*- coding: utf-8 -*-
from functools import wraps
from datetime import datetime
import os
import re

from mailpy.view import MailView
from mailpy.response import TextMailResponse
from mailpy.exceptions import MailViewError
from mailpy.contrib.filelock import FileLock, FileLockTimeout
from mailpy.contrib.pelican.api import PelicanAPI
from mailpy.contrib.pelican.utils import stringify, slugify
from mailpy.contrib.pelican.content import RstArticle
from mailpy.contrib.pelican.exceptions import FileNotFound, FileAlreadyExists, UnknownFileFormat

__all__ = ('PelicanMailView',)


def lock(fun):
    """Lock decorator"""
    @wraps(fun)
    def wrap(obj, request, *args, **kwargs):
        flock = FileLock(obj.lock_file)

        try:
            flock.acquire()
        except FileLockTimeout as exc:
            raise MailViewError(request, 'Locked: %s' % exc, status_code=423)

        try:
            return fun(obj, request, *args, **kwargs)
        finally:
            flock.release()

    return wrap


class PelicanMailView(MailView):
    """
    Pelican mail view.
    """
    settings_file = NotImplemented
    article_class = RstArticle  # Used only for new articles
    article_file_name = '%Y-%m-%d-{slug}'  # Without extension; valid placeholders: {slug} and strftime() directives
    papi_class = PelicanAPI
    papi_settings = ()
    site_url = None
    authors = ()
    lock_file = None
    _valid_content_maintypes = frozenset(('text', 'image', 'audio', 'video', 'application'))
    _valid_text_content_type = frozenset(('text/plain',))
    _ignored_file_content_types = frozenset(('text/x-vcard', 'text/vcard',
                                             'application/pgp-signature',
                                             'application/x-pkcs12',
                                             'application/x-pkcs7-signature',
                                             'application/x-pkcs7-mime',
                                             'application/pkcs12',
                                             'application/pkcs7-signature',
                                             'application/pkcs7-mime'))

    def __init__(self):
        super(PelicanMailView, self).__init__()
        # Initialize the Pelican API
        self.papi = self.papi_class(self.settings_file, **dict(self.papi_settings))
        self.lock_file = self.lock_file or self.settings_file + '.lock'

    @property
    def _site_url(self):
        """Return site URL"""
        return self.site_url or self.papi.site_url

    def _get_author_from_email(self, email, default=None):
        """Helper for mail views"""
        for author, emails in self.authors:
            if email in emails:
                return author

        return default

    def _create_article_slug(self, title, articles):
        """Create unique article slug from title"""
        slug = orig_slug = slugify(title)
        slugs = self.papi.get_article_slugs(articles=articles)  # dict {slug: article}
        i = 1

        while slug in slugs:
            i += 1
            slug = '%s-%d' % (orig_slug, i)

        return slug

    def __create_article_filename(self, slug, addon=''):
        """Generate new article filename"""
        name = datetime.now().strftime(self.article_file_name)
        filename = name.format(slug=slug)

        return '%s%s%s' % (filename, addon, self.article_class.extension)

    def _create_article_filename(self, slug, articles):
        """Create new unique filename from title"""
        filename = self.__create_article_filename(slug)
        filenames = set(a.filename for a in articles)
        i = 1

        while filename in filenames:
            i += 1
            filename = self.__create_article_filename(slug, addon='-%d' % i)

        return filename

    def _create_article(self, title):
        """Create new PelicanArticle object"""
        articles = self.papi.articles
        slug = self._create_article_slug(title, articles)
        filename = self._create_article_filename(slug, articles)

        return self.article_class(self.papi.content_path, filename)

    def _create_static_filename(self, maintype, orig_filename):
        """Create proper filename for static file according to original filename"""
        if maintype == 'image':
            directory = self.papi.images_dir
        else:
            directory = self.papi.files_dir

        orig_filename = stringify(orig_filename).strip()

        if not orig_filename:
            orig_filename = 'noname'

        filename = os.path.join(directory, orig_filename)
        static_files = set(self.papi.get_static_files(directory))
        name, ext = os.path.splitext(filename)
        i = 1

        while filename in static_files:
            i += 1
            filename = '%s-%d%s' % (name, i, ext)

        return filename

    @staticmethod
    def _get_msg_text(msg_part, fallback_charset=None):
        """Return text in mime message converted into unicode str"""
        content = msg_part.get_payload(decode=True)
        charset = msg_part.get_content_charset() or fallback_charset or 'ascii'

        return content.decode(charset, 'replace')

    @staticmethod
    def _edit_msg_text(text):
        """Process text extracted from mail message and return text suitable for article content"""
        # Fix automatic links injected by mail clients, e.g. "<www.google.com> <http://www.google.com>"
        return re.sub(r'([^\s]+) <([\w\+]+:/*)?\1/?>(?!`_)', r'\1', text)

    def _get_msg_content(self, msg, article):
        """Parse message and retrieve text content and additional file attachments"""
        text = []
        files = []

        for part in msg.walk():
            content_type = part.get_content_type()
            maintype = part.get_content_maintype()

            if maintype in self._valid_content_maintypes:
                orig_filename = part.get_filename()

                if orig_filename:  # Attached file
                    if content_type in self._ignored_file_content_types:
                        continue  # Ignore vcard, digital signatures and stuff like this

                    filename = self._create_static_filename(maintype, orig_filename)

                    if maintype == 'image':
                        text_data = article.image(orig_filename, '{filename}/%s' % filename)
                    else:
                        text_data = article.internal_link(orig_filename, '{filename}/%s' % filename)

                    text.append(text_data)
                    files.append(self.papi.get_static_file(filename, content=part.get_payload(decode=True),
                                                           encoding=part.get_content_charset()))  # Store raw

                elif content_type in self._valid_text_content_type:  # Article text
                    msg_text = self._get_msg_text(part, msg.get_charset())  # Decode using content charset
                    text.append(self._edit_msg_text(msg_text))

        return '\n\n'.join(text), files

    def _get_article_metadata(self, request, article, text):
        """Create article metadata"""
        metadata = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'authors': self._get_author_from_email(request.sender, request.sender),
        }
        new_text, parsed_metadata = article.get_text_metadata(text)
        metadata.update(parsed_metadata)

        return new_text, metadata

    @staticmethod
    def _save_article(request, article, static_files):
        """Save article file and all static files; Delete already created files in case of an error"""
        created = []

        try:
            for static_file in static_files:
                static_file.save()
                created.append(static_file.full_path)

            try:
                article.save()
            except FileAlreadyExists:
                raise MailViewError(request, 'Article "%s" already exists' % article, status_code=406)
            else:
                created.append(article.full_path)
        except Exception as exc:
            for f in created:
                # noinspection PyBroadException
                try:
                    os.remove(f)
                except:
                    pass

            raise exc  # Re-raise original exception

        return created

    # noinspection PyUnusedLocal
    @staticmethod
    def _delete_article(request, article):
        """Delete article"""
        # TODO: delete related static files
        article.delete()

        return [article.full_path]

    def _get_article(self, request, title_or_filename):
        """Fetch existing article according to title or filename"""
        try:
            try:
                return self.papi.get_article(title_or_filename)
            except UnknownFileFormat:
                return self.papi.get_article_by_slug(slugify(title_or_filename.lstrip('Re: ')))
        except FileNotFound:
            raise MailViewError(request, 'Article "%s" was not found' % title_or_filename, status_code=404)

    def _commit_and_publish(self, commit_msg, **commit_kwargs):
        """Commit to git if repo_path is set and update html files"""
        if commit_msg and self.papi.repo_path:
            self.papi.commit(commit_msg, **commit_kwargs)

        self.papi.publish()

    def _response(self, request, msg, **kwargs):
        """Create nice mail response"""
        site_url = self.site_url

        if site_url and site_url.startswith('http'):
            msg += '\n\n--\n%s\n' % site_url

        return TextMailResponse(request, msg, **kwargs)

    def get(self, request):
        """Return list of blog posts or content of one blog post depending on the subject"""
        filename = request.subject.strip()

        if filename:
            article = self._get_article(request, filename)
            res = article.load()
        else:
            res = '\n'.join(a.filename for a in self.papi.articles)

        return self._response(request, res)

    @lock
    def post(self, request):
        """Create new blog post, commit and rebuild the html output"""
        title = request.subject.strip()

        if not title:
            raise MailViewError(request, 'Subject (title) is required')

        article = self._create_article(title)
        text, static_files = self._get_msg_content(request, article)
        text, metadata = self._get_article_metadata(request, article, text)
        article.compose(title, text, metadata)
        created = self._save_article(request, article, static_files)
        commit_msg = 'Added article %s' % article.filename

        if static_files:
            commit_msg += ' + static files:\n\t+ %s' % '\n\t+ '.join(i.filename for i in static_files)

        self._commit_and_publish(commit_msg, add=created)
        sep = '*' * 40
        out = 'Article "%s" was successfully created\n\n%s\n%s\n%s' % (article.filename, sep, article.content, sep)

        return self._response(request, out)

    @lock
    def delete(self, request):
        """Delete one blog post, commit and rebuild the html output"""
        filename = request.subject.strip()

        if not filename:
            raise MailViewError(request, 'Subject (filename) is required')

        article = self._get_article(request, filename)
        deleted = self._delete_article(request, article)

        self._commit_and_publish('Deleted article %s' % article, remove=deleted)

        return self._response(request, 'Article "%s" was successfully deleted' % article.filename)
