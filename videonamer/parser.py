#!/usr/bin/env python

"""FileParser for tvnamer/movienamer
"""

import os
import re
import logging

from config import Config
from utils import applyCustomInputReplacements

from tvnamer_exceptions import InvalidFilename

__all__ = ('FileParser', )

log = logging.getLogger(__name__)

class FileParser(object):
    """Deals with parsing of filenames
    """
    __unique_objects = {}
    
    def __new__(cls, config_key=''):
        try:
            return cls.__unique_objects['config_key']
        except KeyError:
            pass
        
        log.debug("FileParser.__new__( %s )" % config_key)
        self = super(FileParser, cls).__new__(cls, config_key=config_key)
        cls.__unique_objects['config_key'] = self
        return self

    def __init__(self, config_key='filename_patterns'):
        self._compileRegexs(config_key)

    def _compileRegexs(self, config_key):
        """Takes episode_patterns from config, compiles them all
        into self.compiled_regexs
        """
        self.compiled_regexs = []
        for cpattern in Config[config_key]:
            try:
                cregex = re.compile(cpattern, re.VERBOSE)
            except re.error, errormsg:
                log.warn("Invalid episode_pattern (error: %s)\nPattern:\n%s"
                     % (errormsg, cpattern))
            else:
                self.compiled_regexs.append(cregex)

    def parse(self, filename):
        """Runs path via configured regex, extracting data from groups.
        Returns an EpisodeInfo instance containing extracted data.
        """
        name = applyCustomInputReplacements(filename)

        for cmatcher in self.compiled_regexs:
            match = cmatcher.match(name)
            if match is not None:
                return match

        else:
            emsg = "Cannot parse %r" % name
            if len(Config['input_filename_replacements']) > 0:
                emsg += " (originally: %s)" % os.path.basename(filename)
            raise InvalidFilename(emsg)
