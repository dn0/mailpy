# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import fnmatch

from pelican.settings import read_settings
from pelican import Pelican

from mailpy.contrib.git import Git, GitError
from .exceptions import PelicanAPIError, FileNotFound, MultipleFilesFound, UnknownFileFormat
from .content import ARTICLE_CLASSES, PelicanContentFile, pelican_article

__all__ = ('PelicanAPI',)


class PelicanAPI(object):
    """
    Pelican blog management API.
    repo_path is used by the commit() method (git)
    images_dir and files_dir are directory names inside content path.
    """
    article_classes = ARTICLE_CLASSES
    static_file_class = PelicanContentFile

    def __init__(self, settings_file, repo_path=None, images_dir='images', files_dir='files'):
        if repo_path is True:
            repo_path = os.path.abspath(os.path.dirname(settings_file))

        self.repo_path = repo_path
        self.images_dir = images_dir
        self.files_dir = files_dir
        self.settings = read_settings(settings_file)
        self.pelican = Pelican(self.settings)
        self.article_extensions = tuple([ext for cls in self.article_classes for ext in cls.file_extensions])

    def article_class(self, content_path, filename, **kwargs):
        """Chooses PelicanArticle class according to file extension and returns article instance"""
        kwargs['supported_classes'] = self.article_classes

        return pelican_article(content_path, filename, **kwargs)

    @property
    def content_path(self):
        """Pelican content directory"""
        return self.settings['PATH']

    @property
    def output_path(self):
        """Pelican content directory"""
        return self.settings['OUTPUT_PATH']

    @property
    def site_url(self):
        """Pelican site URL"""
        return self.settings['SITEURL']

    def _include_path(self, path, extensions):
        """Inclusion logic for .get_files() - based on pelican.generators.Generator._include_path()"""
        basename = os.path.basename(path)
        ignores = self.settings['IGNORE_FILES']

        if any(fnmatch.fnmatch(basename, ignore) for ignore in ignores):
            return False

        if extensions is False or basename.endswith(extensions):
            return True

        return False

    def _get_files(self, paths, exclude=(), extensions=None, file_class=PelicanContentFile):
        """Return a list of files to use, based on rules - based on pelican.generators.Generator.get_files()"""
        # group the exclude dir names by parent path, for use with os.walk()
        exclusions_by_dirpath = {}
        files = []

        for e in exclude:
            parent_path, subdir = os.path.split(os.path.join(self.content_path, e))
            exclusions_by_dirpath.setdefault(parent_path, set()).add(subdir)

        for path in paths:
            try:
                # careful: os.path.join() will add a slash when path == ''.
                root = os.path.join(self.content_path, path) if path else self.content_path

                if os.path.isdir(root):
                    for dirpath, dirs, temp_files in os.walk(root, followlinks=True):
                        for e in exclusions_by_dirpath.get(dirpath, ()):
                            if e in dirs:
                                dirs.remove(e)

                        reldir = os.path.relpath(dirpath, self.content_path)

                        for f in temp_files:
                            if reldir == '.':
                                fp = f
                            else:
                                fp = os.path.join(reldir, f)
                            if self._include_path(fp, extensions):
                                files.append(file_class(self.content_path, fp))

                elif os.path.exists(root) and self._include_path(path, extensions):
                    files.append(file_class(self.content_path, path))  # can't walk non-directories
            except UnknownFileFormat:
                continue

        return files

    def commit(self, msg, add=(), remove=()):
        """Run git add <files> or git rm <files> and git commit -m <msg> inside content path"""
        if not self.repo_path:
            raise PelicanAPIError('git support is disabled (repo_path is not set)')

        assert add or remove, 'nothing to do'

        git = Git(self.repo_path)

        try:
            if add:
                # noinspection PyArgumentList
                git.add(*add)
            if remove:
                # noinspection PyArgumentList
                git.rm(*remove)

            return git.commit(msg)
        except GitError as exc:
            try:
                git.reset()
            except GitError:
                pass

            raise exc  # Re-raise the original error

    def publish(self):
        """Update pelican output folder"""
        self.pelican.run()

    def get_article(self, filename, **kwargs):
        """Return pelican article object according to filename extension"""
        article = self.article_class(self.content_path, filename, **kwargs)

        if not article.exists():
            raise FileNotFound(article)

        return article

    def get_articles(self):
        """Return list of available articles filtered by file extensions"""
        return self._get_files(self.settings['ARTICLE_PATHS'], exclude=self.settings['ARTICLE_EXCLUDES'],
                               extensions=self.article_extensions, file_class=self.article_class)

    def get_static_file(self, filename, **kwargs):
        """Return pelican content file object"""
        return self.static_file_class(self.content_path, filename, **kwargs)

    def get_static_files(self, *directories):
        """Return list of static files inside directories specified as parameter"""
        return self._get_files(directories, extensions=False, file_class=self.static_file_class)

    @property
    def articles(self):
        """Return list of available articles"""
        return self.get_articles()

    @property
    def images(self):
        """Return list of files inside images folder"""
        return self.get_static_files(self.images_dir)

    @property
    def files(self):
        """Return list of files inside files folder"""
        return self.get_static_files(self.files_dir)

    def get_article_slugs(self, articles=None):
        """Return dictionary with slugs mapped to to article objects"""
        if articles is None:
            articles = self.articles

        settings = self.settings

        return {a.get_path_metadata(settings)['slug']: a for a in articles}

    def get_articles_by_slug(self, slug, articles=None):
        """Return pelican article objects according to slug name"""
        slug_len = len(slug)
        article_slugs = self.get_article_slugs(articles=articles)

        def slug_match(x):
            return x.startswith(slug) and (x == slug or x[slug_len:].lstrip('-').isdigit())

        return [a for s, a in article_slugs.items() if slug_match(s)]

    def get_article_by_slug(self, slug, articles=None):
        """Return pelican article object according to slug name"""
        article_list = self.get_articles_by_slug(slug, articles=articles)

        if article_list:
            if len(article_list) > 1:
                raise MultipleFilesFound
        else:
            raise FileNotFound

        return article_list[0]
