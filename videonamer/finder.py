#!/usr/bin/env python

"""FileFinder for tvnamer/movienamer
"""
__all__ = ('FileFinder', )

import os
import re
import logging

from config import Config

log = logging.getLogger(__name__)
#log.setLevel(logging.WARNING)


def FileFinder(paths, _marked_paths=None, _recursive=True):
    """Given a file, it will verify it exists. Given a folder it will descend
    one level into it and return a list of files, unless the recursive argument
    is True, in which case it finds all files contained within the path.

    The with_extension argument is a list of valid extensions, without leading
    spaces. If an empty list (or None) is supplied, no extension checking is
    performed.

    The filename_blacklist argument is a list of regexp strings to match
    against the filename (minus the extension). If a match is found, the file
    is skipped (e.g. for filtering out "sample" files). If [] or None is
    supplied, no filtering is done
    """

    if _marked_paths is None:
        _marked_paths = set()

    for path in paths:
        path = path[:-1] if path[-1] == os.pathsep else path
        filename = os.path.basename(path)

        if not os.access(path, os.R_OK):
            log.error("Inaccessible path %s" % path)
            continue           
        if _blacklistedFilename(filename):
            log.debug("Skipping blacklisted file %s" % filename)
            continue

        if os.path.isdir(path):
            path = _marked_path(path, _marked_paths)
            if not path:
                continue
            
            if _recursive:
                for subtree_path in FileFinder((os.path.join(path, name) 
                                                for name in os.listdir(path)),
                                               _marked_paths=_marked_paths,
                                               _recursive=Config['recursive']):
                    yield subtree_path

            if Config['library'] and not _library_blacklist(filename):
                yield path

        elif os.path.isfile(path):
            if not _checkExtension(path):
                log.debug("Skipping blacklisted extension in %s" % filename)
                continue
        
            path = _marked_path(path, _marked_paths)
            if path:
                yield path
        else:
            log.error("Skipping invalid path %s" % path)
            continue


def _marked_path(path, _marked_paths):
    path = os.path.abspath(path)
    if path in _marked_paths:
        return None
    
    _marked_paths.add(path)
    return path

def _checkExtension(fname):
    """Checks if the file extension is blacklisted in valid_extensions
    """
    with_extension = Config['valid_extensions']
    
    if len(with_extension) == 0:
        return True

    _, extension = os.path.splitext(fname)
    for cext in with_extension:
        cext = ".%s" % cext
        if extension == cext:
            return True
    else:
        return False

def _blacklistedFilename(fname):
    """Checks if the filename (excl. ext) matches filename_blacklist
    """
    filename_blacklist = Config['filename_blacklist']
    
    fname, _ = os.path.splitext(fname)

    for fblacklist in filename_blacklist:
        if "is_regex" in fblacklist and fblacklist["is_regex"]:
            if re.match(fblacklist["match"], fname):
                return True
        else:
            if fname.find(fblacklist["match"]) != -1:
                return True
    else:
        return False

def _library_blacklist(fname):
    """Checks if the filename (excl. ext) matches library_blacklist
    """
    library_blacklist = Config['library_blacklist']
    
    fname, _ = os.path.splitext(fname)
    for fblacklist in library_blacklist:
        if "is_regex" in fblacklist and fblacklist["is_regex"]:
            if re.match(fblacklist["match"], fname):
                return True
        else:
            if fname.find(fblacklist["match"]) != -1:
                return True
    else:
        return False
