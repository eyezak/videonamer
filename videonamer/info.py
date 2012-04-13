#!/usr/bin/env python

"""Utilities for tvnamer, including filename parsing
"""

import os
import logging

from config import Config
from parser import FileParser
from utils import (applyCustomOutputReplacements,
                   applyCustomFullpathReplacements,
                   makeValidFilename,
                   applyCustomInputReplacements)

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)

class MetaBaseInfo(type):
    def __new__(mcls, clsname, bases, clsdict):
        cls =  super(MetaBaseInfo, mcls).__new__(mcls, clsname, bases, clsdict)
        
        try:
            base = [ base for base in bases if base.__name__ == 'BaseInfo' ][0]
        except IndexError:
            return cls

        try:
            mediatype = clsdict['_media_type']
        except KeyError:
            raise NotImplementedError('%s._media_type' % clsname)

        log.debug("Registered Info<%s> for %s" % (clsname, mediatype))
        base._media_types[mediatype] = cls        
        return cls

class BaseInfo(object):
    """Stores information (movietitle), and contains
    logic to generate new name
    """
    
    __metaclass__ = MetaBaseInfo
    _media_types = {}

    def __init__(self, path):
        self.filepath, self.filename = os.path.split(path)
        self.is_dir = os.path.isdir(path)
        if self.is_dir:
            self.extension = ""
        else:
            self.filename, self.extension = os.path.splitext(self.filename)
        
        match = FileParser(config_key=self._parser_key).parse(self.filename)
        
        self._init_from_match(match)

    @classmethod
    def get_media_cls(cls, media_type):
        try:
            return cls._media_types[media_type]
        except KeyError:
            raise NotImplementedError(media_type)

    @classmethod
    def get_media_classes(cls):
        return cls._media_types.values()

    @classmethod
    def _from_path(cls, path):
        raise NotImplementedError()

    def get_format_data(self):
        raise NotImplementedError()
    
    def __repr__(self):
        return u"<%s: %s>" % (
            self.__class__.__name__,
            ', '.join(self.unique_info()))

    def unique_info(self):
        try:
            unique_attrs = self._unique_attrs
        except AttributeError as e:
            raise NotImplementedError(e)

        for attr in unique_attrs:
            value = getattr(self, attr, None)
            if value:
                yield "%s" % value

    @property
    def fullpath(self):
        return os.path.join(self.filepath, self.filename)

    @property
    def fullfilename(self):
        return u''.join((self.filename, self.extension))

    def generate_filename(self):
        if self.is_dir:
            return self.generate_dirname()

        if callable(self._filename_key):
            key = self._filename_key()
        else:
            key = self._filename_key
        try:
            formatstr = Config[key]
        except KeyError:
            raise NotImplementedError(key)

        fname = formatstr % self.__dict__

        if Config['lowercase_filename']:
            fname = fname.lower()

        if len(Config['output_filename_replacements']) > 0:
            # Only apply replacements to filename, not extension
            log.info("Before custom output replacements: %s" % fname)
            splitname, splitext = os.path.splitext(fname)
            newname = applyCustomOutputReplacements(splitname)
            fname = newname + splitext
        
        fname = makeValidFilename(fname)
        log.debug("Generated name '%s' for %s" % (fname, self))
        return fname

    def generate_dirname(self):
        if callable(self._dirname_key):
            key = self._dirname_key()
        else:
            key = self._dirname_key
        try:
            formatstr = Config[key]
        except KeyError:
            raise NotImplementedError(key)

        dirname = formatstr % self.__dict__

        if Config['move_files_lowercase_destination']:
            dirname = dirname.lower()
        
        if len(Config['move_files_fullpath_replacements']) > 0:
            log.info("Before custom output replacements: %s" % dirname)
            dirname = applyCustomFullpathReplacements(dirname)
        
        log.debug("Generated path '%s' for %s" % (dirname, self))
        return dirname
    
    def generate_path(self):
        return os.path.join(Config[self._destination_key], 
                            self.generate_dirname()) 
