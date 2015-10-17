# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re
import os
import codecs

from pelican.readers import parse_path_metadata

from .exceptions import FileNotFound, FileAlreadyExists, UnknownFileFormat

__all__ = ('PelicanContentFile', 'PelicanArticle', 'RstArticle', 'MarkdownArticle')


class PelicanContentFile(object):
    """
    Base container for any pelican content file.
    This is basically a filename with some advanced attributes.
    The content attribute should always be stored as byte str.
    """
    encoding = None

    def __init__(self, content_path, filename, content=None, encoding=None):
        self.content_path = content_path
        self.filename = filename
        self.extension = os.path.splitext(filename)[1]
        self._content = content
        self.encoding = encoding or self.encoding

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.filename.encode('ascii', errors='backslashreplace'))

    def __str__(self):
        return '%s' % self.filename

    def __unicode__(self):
        return '%s' % self.filename

    def __eq__(self, other):
        return self.filename == other

    def __ne__(self, other):
        return self.filename != other

    def __hash__(self):
        return self.filename.__hash__()

    def __nonzero__(self):
        return bool(self.filename)
    __bool__ = __nonzero__

    @property
    def content(self):
        if self._content is None:
            raise ValueError('file content is not loaded')
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    @property
    def full_path(self):
        """Get file full path"""
        return os.path.abspath(os.path.join(self.content_path, self.filename))

    def exists(self):
        """Return True if file exists on FS"""
        return os.path.isfile(self.full_path)

    # noinspection PyMethodMayBeStatic
    def _delete(self, file_path):
        """Actual file delete operation"""
        os.remove(file_path)

    def delete(self):
        """Remove file from disk"""
        if not self.exists():
            raise FileNotFound(self)

        self._delete(self.full_path)

    def _load(self, file_path):
        """Actual file read operation"""
        with codecs.open(file_path, mode='rb', encoding=self.encoding) as fp:
            return fp.read()

    def load(self):
        """Load and return file content from disk"""
        if not self.exists():
            raise FileNotFound(self)

        self.content = self._load(self.full_path)

        return self.content

    def _save(self, file_path, content):
        """Actual file write operation"""
        with codecs.open(file_path, mode='wb', encoding=self.encoding) as fp:
            fp.write(content)

    def save(self):
        """Write file content to disk"""
        if self.exists():
            raise FileAlreadyExists(self)

        self._save(self.full_path, self.content)


class PelicanArticle(PelicanContentFile):
    """
    Base class for article formats.
    The content should always be a unicode str.
    """
    encoding = 'utf-8'
    extension = NotImplemented
    re_metadata = NotImplemented

    def _load(self, file_path):
        """Read text file content from disk (pelican style)"""
        content = super(PelicanArticle, self)._load(file_path)

        if content[0] == codecs.BOM_UTF8.decode(self.encoding):
            content = content[1:]

        return content

    def get_path_metadata(self, settings):
        """Parse file metadata from file's path"""
        return parse_path_metadata(self.filename, settings=settings)

    def _parse_metadata(self, metadata, line):
        """Parse metadata from one line of text and update the metadata dict"""
        found = self.re_metadata.match(line)

        if found:
            metadata[found.group(1).lower()] = found.group(2)
            return True
        else:
            return False

    def get_text_metadata(self, text):
        """Separate metadata from text and return (new text, metadata) tuple"""
        metadata = {}
        new_text = '\n'.join(line for line in text.splitlines() if not self._parse_metadata(metadata, line))

        return new_text, metadata

    def _compose(self, title, text, metadata):
        """Return new content from supplied parameters"""
        raise NotImplementedError

    def compose(self, title, text, metadata):
        """Create and set new content"""
        self.content = self._compose(title, text, metadata)

        return self.content

    def internal_link(self, text, uri):
        raise NotImplementedError

    def image(self, alt, uri):
        raise NotImplementedError


class RstArticle(PelicanArticle):
    """
    Article stored in reStructuredText format.
    """
    extension = '.rst'
    file_extensions = ('rst',)
    re_metadata = re.compile(r'^:(\w+):\s+(.+)$')

    def _compose(self, title, text, metadata):
        return '%(title)s\n%(title_underscore)s\n\n%(metadata)s\n\n%(text)s\n' % {
            'title': title,
            'title_underscore': '#' * len(title),
            'metadata': '\n'.join(':%s: %s' % i for i in metadata.items()),
            'text': text,
        }

    def internal_link(self, text, uri):
        return '`%s <%s>`_' % (text, uri)

    def image(self, alt, uri):
        return '.. image:: %s\n    :alt: %s' % (uri, alt)


class MarkdownArticle(PelicanArticle):
    """
    Article stored in markdown format.
    """
    extension = '.md'
    file_extensions = ('md', 'markdown', 'mkd', 'mdown')
    re_metadata = re.compile(r'^  ([A-Z]\w*):\s+(.+)$')

    def _compose(self, title, text, metadata):
        metadata['title'] = title

        return '%(metadata)s\n\n# %(title)s\n\n%(text)s\n' % {
            'metadata': '\n'.join('  %s: %s' % (k.title(), v) for k, v in metadata.items()),
            'title': title,
            'text': text,
        }

    def internal_link(self, text, uri):
        return '[%s](%s)' % (text, uri)

    def image(self, alt, uri):
        return '![%s](%s)' % (alt, uri)


ARTICLE_CLASSES = (RstArticle, MarkdownArticle)


def pelican_article(content_path, filename, **kwargs):
    """Return PelicanArticle object according to file extensions"""
    supported_classes = kwargs.pop('supported_classes', ARTICLE_CLASSES)
    ext = os.path.splitext(filename)[1].lstrip('.')

    for cls in supported_classes:
        if ext in cls.file_extensions:
            return cls(content_path, filename, **kwargs)

    raise UnknownFileFormat('Unsupported article format: %s' % ext)
