#!/usr/bin/env python

"""Main movienamer utility functionality
"""
__all__ = ( 'init', 'run', )

import os
import sys

import logging
logging.basicConfig(level=logging.INFO,
                    stream=sys.stderr,
                    format="%(filename)s:%(lineno)d: %(msg)s")

try:
    import json
except ImportError:
    import simplejson as json

import tmdb3

import cliarg_parser
from config_defaults import defaults

from config import Config
import config_defaults
from finder import FileFinder
import renamer
from info import BaseInfo
import tv, movie

from tvnamer_exceptions import (ShowNotFound, SeasonNotFound, EpisodeNotFound,
EpisodeNameNotFound, UserAbort, InvalidMatch, NoValidFilesFoundError,
InvalidFilename, DataRetrievalError)

log = logging.getLogger(__name__)
#log.setLevel(logging.WARN)

def doRenameFile(path, newName):
    """Renames the file. path should be the original path,
    newName should be string containing new filename.
    """
    try:
        renamer.rename_file(path, newName, 
                            force=Config['overwrite_destination_on_rename'])
    except OSError, e:
        log.exception(e)


def doMoveFile(path, destDir = None, destFilepath = None):
    """Moves file to destDir, or to destFilepath
    """

    if (destDir is None and destFilepath is None) or \
       (destDir is not None and destFilepath is not None):
        raise ValueError("Specify only destDir or destFilepath")

    if not Config['move_files_enable']:
        raise ValueError("move_files feature is disabled but doMoveFile was called")

#    if Config['move_files_destination'] is None:
#        raise ValueError("Config value for move_files_destination cannot be None"
#                         "if move_files_enabled is True")

    try:
        return renamer.rename_path(
            path,
            new_path = destDir,
            new_fullpath = destFilepath,
            always_move = Config['always_move'],
            force = Config['overwrite_destination_on_move'])

    except OSError, e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception(e)
        else:
            log.error(e)


def confirm(question, options, default = "y"):
    """Takes a question (string), list of options and a default value (used
    when user simply hits enter).
    Asks until valid option is entered.
    """
    # Highlight default option with [ ]
    options_str = []
    for x in options:
        if x == default:
            x = "[%s]" % x
        if x != '':
            options_str.append(x)
    options_str = "/".join(options_str)

    while True:
        print "%s (%s) " % (question, options_str),
        try:
            ans = raw_input().strip()
        except KeyboardInterrupt, errormsg:
            print "\n", errormsg
            raise UserAbort(errormsg)

        if ans in options:
            return ans
        elif ans == '':
            return default


def processFile(info):
    """Gets info name, prompts user for input
    """
    log.debug ("Detected: %s from %s" % (info, info.fullfilename))
    
    move_files_only = Config['move_files_only']
    move_files = Config['move_files_enable']
    question = None
    
    info.populate_from_db(force_name=Config['force_name'], uid=Config['force_id'])

    if move_files_only:
        new_name = info.fullfilename
    else:
        new_name = info.generate_filename()
        question = "Rename"

    if new_name == info.fullfilename:
        log.debug("Existing filename is correct: %s" % info.fullfilename)
        if not move_files:
            return
    
    if move_files:
        new_path = info.generate_path()
        new_filepath = os.path.join(new_path, new_name)
        if new_filepath == info.fullpath:
            log.debug("Existing filepath is correct: %s" % info.fullpath)
            return

        log.info("Old filename: %s" % info.fullfilename)        
        log.info("New path: %s" % new_filepath)
        question = ("%s / Move" % question) if question is None else "Move"
    else:
        log.info("Old filename: %s" % info.fullfilename)
        log.info("New filename: %s" % new_name) 
    
    if not Config['always_rename']:
        ans = confirm("%s?" % question,
                      options = ['y', 'n', 'a', 'q'],
                      default = 'y')

        if ans == "a":
            log.info("Always renaming")
            Config['always_rename'] = True
        elif ans == "q":
            log.info("Quitting")
            raise UserAbort("User exited with q")
        elif ans == "y":
            log.info("Renaming")
        elif ans == "n":
            log.info("Skipping")
            return
        else:
            log.debug("Invalid input, skipping")
            return
    
    if move_files:
        doMoveFile(info.fullpath, destFilepath = new_filepath)
    else:
        doRenameFile(info.fullpath, new_name)

def run(paths):
    """Main movienamer function, takes an array of paths, does stuff.
    """

    log.info("Starting movienamer")

    info_cls = BaseInfo.get_media_cls(Config['media_type'])
    file_finder = FileFinder(paths)

    #print
    for filepath in file_finder:
        log.debug("Found Path: %s" % filepath)           
        for info_cls in BaseInfo.get_media_classes():
            try:
                info = info_cls(filepath)
                processFile(info)

            except (InvalidFilename, InvalidMatch,
                    ShowNotFound, SeasonNotFound,
                    EpisodeNotFound, EpisodeNameNotFound,
                    DataRetrievalError) as e:
                
                if log.getEffectiveLevel() <= logging.DEBUG:
                    log.debug(e, exc_info=True)
                else:
                    log.info(e)

            else:
                break
 
        else:
            if not Config['skip_file_on_error']:
                break
            
            log.warn("Skipping file <%s>" % info.fullfilename)
            #if log.getEffectiveLevel() > logging.WARNING:
            #    continue
        
        #print

    log.info("Done")


def load_config(verbose=True, default_configuration=None):
    if verbose:
        logging.basicConfig(
            level = logging.DEBUG,
            format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig()
    
    if default_configuration is None:
        default_configuration = os.path.expanduser("~/.videonamer.json")
    if os.path.isfile(default_configuration):
        # No --config arg, so load default config if it exists
        configToLoad = default_configuration
    else:
        # No arg, nothing at default config location, don't load anything
        configToLoad = None
    
    if configToLoad is not None:
        log.info("Loading config: %s" % (configToLoad))
        try:
            loadedConfig = json.load(open(configToLoad))
        except ValueError, e:
            log.critical("Error loading config: %s" % e)
            sys.exit(1) 

    return loadedConfig

def process_config():
    tmdb3.DEBUG = Config['verbose']
    
    # Process values
    if Config['batch']:
        Config['always_rename'] = True
        Config['select_first'] = True
    if Config["move_files_only"] and not Config["move_files_enable"]:
        log.critical("Parameter move_files_enable cannot be set to false while parameter move_only is set to true.")
        sys.exit(1)
    if Config['move_files_enable'] and Config['library']:
        log.critical("Parameters move_files_enabled and library cannot both be true.")
        sys.exit(1)

    for key in ('movie_destination', 'tv_destination'):
        Config[key] = os.path.abspath(Config[key])



def init(**kwds):
    Config.update(cliarg_parser.getCommandlineParser(defaults).defaults)
    Config.update(load_config())
    Config.update(**kwds)
    process_config()

def main():
    """Parses command line arguments, displays errors from movienamer in terminal
    """
    opter = cliarg_parser.getCommandlineParser(defaults)
    opts, args = opter.parse_args()

    defaults.update(load_config())           
    opter = cliarg_parser.getCommandlineParser(defaults)
    opts, args = opter.parse_args()

    # Decode args using filesystem encoding (done after config loading
    # as the args are reparsed when the config is loaded)
    args = [x.decode(sys.getfilesystemencoding()) for x in args]

    # Save config argument
    if opts.saveconfig is not None:
        log.info("Saving config: %s" % (opts.saveconfig))
        configToSave = dict(opts.__dict__)
        del configToSave['saveconfig']
        del configToSave['loadconfig']
        del configToSave['showconfig']
        json.dump(
            configToSave,
            open(opts.saveconfig, "w+"),
            sort_keys=True,
            indent=4)

        opter.exit(0)

    # Show config argument
    if opts.showconfig:
        for k, v in opts.__dict__.items():
            print k, "=", str(v)
        return

    # Update global config object
    Config.update(opts.__dict__)
    process_config()

    if len(args) == 0:
        log.error("No filenames or directories supplied")
        sys.exit(1)
    
    try:
        run(paths = sorted(args))
    except NoValidFilesFoundError:
        opter.error("No valid files were supplied")
    except UserAbort, errormsg:
        opter.error(errormsg)

tmdb3.set_key('c27cb71cff5bd76e1a7a009380562c62') #MythTV API Key

if __name__ == '__main__':
    main()
