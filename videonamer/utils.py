#!/usr/bin/env python


import os
import re
import logging
import platform

from config import Config

__all__ = tuple()

log = logging.getLogger(__name__)


class TextToNumber(object):
    numwords = {
                "one":   (1, 1),
                "two":   (1, 2),
                "three": (1, 3),
                "four":  (1, 4),
                "five":  (1, 5),
                "six":   (1, 6),
                "seven": (1, 7),
                "eight": (1, 8),
                "nine":  (1, 9),
                "ten":   (1, 10),
                "eleven":   (1, 11),
                "twelve":   (1, 12),
                "thirteen": (1, 13),
                "fourteen": (1, 14),
                "fifteen":  (1, 15),
                "sixteen":  (1, 16),
                "seventeen": (1, 17),
                "eighteen": (1, 18),
                "nineteen": (1, 19),
                "twenty":   (1, 20),
                "thirty":   (1, 30),
                "fourty":   (1, 40),
                "fifty":   (1, 50),
                "sixty":   (1, 60),
                "seventy":   (1, 70),
                "eightty":   (1, 80),
                "ninety":   (1, 90),
                "hundred":   (1, 10**2),
                "thousand":   (1, 10**3),
                "million":   (1, 10**4),
                "billion":   (1, 10**5),
                "trillion":   (1, 10**6)
               }
    
    pattern = '|'.join(numwords)
    
    def __new__(cls, words):
        result = current = 0      
        for word in words:
            scale, increment = cls.numwords[word.lower()]
            current = current * scale + increment
            if scale > 100:
                result += current
                current = 0
        result += current
        
        return "%d" % result


def same_partition(f1, f2):
    """Returns True if both files or directories are on the same partition
    """
    return os.stat(f1).st_dev == os.stat(f2).st_dev


def delete_file(fpath):
    raise NotImplementedError("delete_file not yet implimented")


def handleYear(year):
    """Handle two-digit years with heuristic-ish guessing

    Assumes 50-99 becomes 1950-1999, and 0-49 becomes 2000-2049

    ..might need to rewrite this function in 2050, but that seems like
    a reasonable limitation
    """

    year = int(year)

    # No need to guess with 4-digit years
    if year > 999:
        return year

    if year < 50:
        return 2000 + year
    else:
        return 1900 + year


def formatEpisodeName(names, join_with):
    """Takes a list of episode names, formats them into a string.
    If two names are supplied, such as "Pilot (1)" and "Pilot (2)", the
    returned string will be "Pilot (1-2)"

    If two different episode names are found, such as "The first", and
    "Something else" it will return "The first, Something else"
    """
    if len(names) == 1:
        return names[0]

    found_names = []
    numbers = []
    for cname in names:
        number = re.match("(.*) \(([0-9]+)\)$", cname)
        if number:
            epname, epno = number.group(1), number.group(2)
            if len(found_names) > 0 and epname not in found_names:
                return join_with.join(names)
            found_names.append(epname)
            numbers.append(int(epno))
        else:
            # An episode didn't match
            return join_with.join(names)

    names = []
    start, end = min(numbers), max(numbers)
    names.append("%s (%d-%d)" % (found_names[0], start, end))
    return join_with.join(names)


def formatEpisodeNumbers(episodenumbers):
    """Format episode number(s) into string, using configured values
    """
    episode_single = Config['episode_single']
    episode_separator = Config['episode_separator']
    
    if len(episodenumbers) == 1:
        epno = episode_single % episodenumbers[0]
    else:
        epno = episode_separator.join(
                episode_single % x for x in episodenumbers)

    return epno


def _applyReplacements(cfile, replacements):
    """Applies custom replacements.

    Argument cfile is string.

    Argument replacements is a list of dicts, with keys "match",
    "replacement", and (optional) "is_regex"
    """
    for rep in replacements:
        if 'is_regex' in rep and rep['is_regex']:
            cfile = re.sub(rep['match'], rep['replacement'], cfile)
        else:
            cfile = cfile.replace(rep['match'], rep['replacement'])

    return cfile


def applyCustomInputReplacements(cfile):
    """Applies custom input filename replacements, wraps _applyReplacements
    """
    return _applyReplacements(cfile, Config['input_filename_replacements'])


def applyCustomOutputReplacements(cfile):
    """Applies custom output filename replacements, wraps _applyReplacements
    """
    return _applyReplacements(cfile, Config['output_filename_replacements'])


def applyCustomFullpathReplacements(cfile):
    """Applies custom replacements to full path, wraps _applyReplacements
    """
    return _applyReplacements(cfile,
                              Config['move_files_fullpath_replacements'])


def replaceInputName(name):
    """allow specified replacements of names

    in cases where default filenames match the wrong series,
    e.g. missing year gives wrong answer, or vice versa

    This helps the TVDB/TMDB query get the right match.
    """
    input_replacements = Config['input_name_replacements']


    for pattern, replacement in input_replacements.iteritems():
        name = re.sub(pattern, replacement, name)

#    for pat, replacement in input_replacements.iteritems():
#        if re.match(pat, name, re.IGNORECASE | re.UNICODE):
#            return replacement
    return name


def replaceOutputName(name):
    """transform TVDB/TMDB names

    after matching from TVDB/TMDB, transform the series name for desired
    abbreviation, etc.

    This affects the output filename.
    """
    output_replacements = Config['output_name_replacements']

    return output_replacements.get(name, name)


def cleanRegexedName(name):
    """Cleans up series name by removing any . and _
    characters, along with any trailing hyphens.

    Is basically equivalent to replacing all _ and . with a
    space, but handles decimal numbers in string, for example:

    >>> cleanRegexedSeriesName("an.example.1.0.test")
    'an example 1.0 test'
    >>> cleanRegexedSeriesName("an_example_1.0_test")
    'an example 1.0 test'
    """
    name = re.sub("(\D)[.](\D)", "\\1 \\2", name)
    name = re.sub("(\D)[.]", "\\1 ", name)
    name = re.sub("[.](\D)", " \\1", name)
    name = name.replace("_", " ")
    name = re.sub("-$", "", name)
    return name.strip()


def makeValidFilename(value, directory=False):
    """
    Takes a string and makes it into a valid filename.

    normalize_unicode replaces accented characters with ASCII equivalent, and
    removes characters that cannot be converted sensibly to ASCII.

    windows_safe forces Windows-safe filenames, regardless of current platform

    custom_blacklist specifies additional characters that will removed. This
    will not touch the extension separator:

        >>> makeValidFilename("T.est.avi", custom_blacklist=".")
        'T_est.avi'
    """
    normalize_unicode = Config['normalize_unicode_filenames']
    windows_safe = Config['windows_safe_filenames']
    custom_blacklist = Config['custom_filename_character_blacklist']
    replace_with = Config['replace_invalid_characters_with']

    if windows_safe:
        # Allow user to make Windows-safe filenames, if they so choose
        sysname = "Windows"
    else:
        sysname = platform.system()

    # If the filename starts with a . prepend it with an underscore, so it
    # doesn't become hidden.

    # This is done before calling splitext to handle filename of ".", as
    # splitext acts differently in python 2.5 and 2.6 - 2.5 returns ('', '.')
    # and 2.6 returns ('.', ''), so rather than special case '.', this
    # special-cases all files starting with "." equally (since dotfiles have
    # no extension)
    if value.startswith("."):
        value = "_" + value

    # Treat extension seperatly
    value, extension = os.path.splitext(value)

    # Remove any null bytes
    value = value.replace("\0", "")

    # Blacklist of characters
    if sysname == 'Darwin':
        # : is technically allowed, but Finder will treat it as / and will
        # generally cause weird behaviour, so treat it as invalid.
        blacklist = r":" if directory else r"/:"
    elif sysname in ['Linux', 'FreeBSD']:
        blacklist = r"" if directory else r"/"
    else:
        # platform.system docs say it could also return "Windows" or "Java".
        # Failsafe and use Windows sanitisation for Java, as it could be any
        # operating system.
        blacklist = r":*?\"<>|" if directory else r"\/:*?\"<>|"

    # Append custom blacklisted characters
    if custom_blacklist is not None:
        blacklist += custom_blacklist

    # Replace every blacklisted character with a underscore
    value = re.sub("[%s]" % re.escape(blacklist), replace_with, value)

    # Remove any trailing whitespace
    value = value.strip()

    # There are a bunch of filenames that are not allowed on Windows.
    # As with character blacklist, treat non Darwin/Linux platforms as Windows
    if sysname not in ['Darwin', 'Linux']:
        invalid_filenames = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2",
        "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1",
        "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
        if value in invalid_filenames:
            value = "_" + value

    # Replace accented characters with ASCII equivalent
    if normalize_unicode:
        import unicodedata
        value = unicode(value)  # cast data to unicode
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')

    # Truncate filenames to valid/sane length.
    # NTFS is limited to 255 characters, HFS+ and EXT3 don't seem to have
    # limits, FAT32 is 254. I doubt anyone will take issue with losing that
    # one possible character, and files over 254 are pointlessly unweidly
    max_len = 254

    if len(value + extension) > max_len:
        if len(extension) > len(value):
            # Truncate extension instead of filename, no extension should be
            # this long..
            new_length = max_len - len(value)
            extension = extension[:new_length]
        else:
            # File name is longer than extension, truncate filename.
            new_length = max_len - len(extension)
            value = value[:new_length]

    return value + extension
