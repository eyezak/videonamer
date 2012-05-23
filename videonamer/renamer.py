#!/usr/bin/env python

"""Renamer for tvnamer/movienamer
"""

import os
import shutil
import logging

from config import Config
from utils import (applyCustomFullpathReplacements,
                   same_partition,
                   delete_file)

__all__ = ('rename_file', 'rename_path')

log = logging.getLogger(__name__)

def rename_file(old_path, new_name, force=False):
    """Renames a file, keeping the path the same.
    """
    test_mode = Config['test_mode']
    
    oldpath = os.path.abspath(old_path)
    filepath, filename = os.path.split(oldpath)
    newpath = os.path.join(filepath, new_name)

    if os.path.isfile(newpath):
        # If the destination exists, raise exception unless force is True
        if not force:
            raise OSError("File %s already exists, "
                          "not forcefully renaming %s"
                          % (newpath, old_path))

    getattr(log, "info" if test_mode or Config['select_first'] else "debug")(
             "Renaming:\n   ** %s\n   => %s" % (old_path, newpath))
    if not test_mode:
        os.rename(old_path, newpath)
    
    return newpath

def rename_path(old_path, new_path=None, new_fullpath=None, force=False,
                  always_copy=False, always_move=False, create_dirs=True):
    """Moves the file to a new path.

    If it is on the same partition,
        it will be moved (unless always_copy is True)
    If it is on a different partition,
        it will be copied.
    If the target file already exists,
        it will raise OSError unless force is True.
    """
    test_mode = Config['test_mode']
    
    old_path = os.path.abspath(old_path)

    if always_copy and always_move:
        raise ValueError("Both always_copy and always_move "
                         "cannot be specified")

    if (new_path is None and new_fullpath is None) or \
       (new_path is not None and new_fullpath is not None):
        raise ValueError("Specify only new_dir or new_fullpath")

    if new_path is not None:
        old_dir, old_filename = os.path.split(old_path)

        # Join new filepath to old one (to handle realtive dirs)
        new_dir = os.path.abspath(os.path.join(old_dir, new_path))

        # Join new filename onto new filepath
        new_fullpath = os.path.join(new_dir, old_filename)

    else:
        old_dir, old_filename = os.path.split(old_path)

        # Join new filepath to old one (to handle realtive dirs)
        new_fullpath = os.path.abspath(os.path.join(old_dir, new_fullpath))

        new_dir = os.path.dirname(new_fullpath)

    if len(Config['move_files_fullpath_replacements']) > 0:
        log.debug("Before custom full path replacements: %s" % (new_fullpath))
        new_fullpath = applyCustomFullpathReplacements(new_fullpath)
        new_dir = os.path.dirname(new_fullpath)

    getattr(log, "info" if test_mode or Config['select_first'] else "debug")(
             "Moving:\n   ** %s\n   => %s" % (old_path, new_fullpath))
    if test_mode:
        return new_fullpath

    if create_dirs:
        log.debug("Creating directory %s" % new_dir)
        try:
            os.makedirs(new_dir)
        except OSError, e:
            if e.errno != 17:
                raise

    if os.path.isfile(new_fullpath):
        # If the destination exists, raise exception unless force is True
        if not force:
            raise OSError("File %s already exists, "
                          "not forcefully moving %s"
                          % (new_fullpath, old_path))

    if same_partition(old_path, new_dir):
        if always_copy:
            # Same partition, but forced to copy
            log.debug("copy %s to %s" % (old_path, new_fullpath))
            shutil.copyfile(old_path, new_fullpath)
        else:
            # Same partition, just rename the file to move it
            log.debug("move %s to %s" % (old_path, new_fullpath))
            os.rename(old_path, new_fullpath)
    else:
        # File is on different partition (different disc), copy it
        log.debug("copy %s to %s" % (old_path, new_fullpath))
        shutil.copyfile(old_path, new_fullpath)
        if always_move:
            # Forced to move file, we just trash old file
            log.debug("Deleting %s" % (old_path))
            delete_file(old_path)

    return new_fullpath
