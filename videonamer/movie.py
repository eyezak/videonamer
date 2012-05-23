#!/usr/bin/env python

"""Utilities for tvnamer, including filename parsing
"""
__all__ = ('MovieInfo',)

import operator
import re
import logging
from urllib2 import URLError

import tmdb3

from config import Config
from utils import (replaceOutputName,
                   cleanRegexedName,
                   replaceInputName,
                   makeValidFilename,
                   TextToNumber)
from tvnamer_exceptions import (ShowNotFound,
                                DataRetrievalError,
                                ConfigValueError,
                                InvalidMatch,
                                MatchingDataNotFound)
from info import BaseInfo
from selector import ConsoleSelector

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)

def release_date(movie):
    try:
        return movie.releasedate.year
    except AttributeError:
        pass

    try:
        return int(movie.releasedate)
    except (TypeError, ValueError):
        return -1

def movie_formatter(movie):
    return "{0} ({1})".format(movie.title.encode("UTF-8", "ignore"),
                              release_date(movie))

def format_genres( genres):
    """Format episode genre(s) into string, using configured values
    """
    return Config['genre_separator'].join(
            Config['genre_single'] % g for g in genres)

class MovieInfo(BaseInfo):
    """Stores information (movietitle), and contains
    logic to generate new name
    """
    
    _media_type = "movie"
    _destination_key = 'movie_destination'
    _dirname_key = 'movie_dirname'
    _unique_attrs = ('movietitle', 'releasedate', 'resolution')
    _parser_key = 'movie_patterns'

    __selector = ConsoleSelector(candidate_formatter=movie_formatter)

#    def __init__(self, movietitle, path=None, extra=None):
#        super(MovieInfo, self).__init__(path=path)

#        self.userrating = None
#        self.genres = None
#        self.extra = extra if extra else {'movietitle': movietitle}
#        self.movietitle = movietitle

#        self.part = self.extra.get("part", None)
#        self.resolution = self.extra.get("resolution", None)

#        try:
#            self.releasedate = int(self.extra.get("releasedate", None))
#        except TypeError:
#            self.releasedate = None

    def _filename_key(self):
        config_key = 'movie_filename'
        if getattr(self, 'resolution', None):
            config_key += '_resolution'
        if getattr(self, 'part', None):
            config_key += '_part'
        return config_key

    def populate_from_db(self, force_name=None, uid=None, adult=False):
        """Queries the moviedb_api
        If series cannot be found, it will warn the user. If the episode is not
        found, it will use the corrected show name and not set an episode name.
        If the site is unreachable, it will warn the user. If the user aborts
        it will catch tvdb_api's user abort error and raise tvnamer's
        """
        def fetch_results(results, max_results):
            fetched = []
            for i, result in enumerate(results):
                log.debug("Search-Result: %s" % result)
                fetched.append(result)
                if i >= max_results:
                    break
            
            return fetched

        def searchMovie(query):

            max_results = Config['max_results']
            log.debug("Searching: %s on themoviedb.com" % query)
            try:
                search_results = tmdb3.searchMovie(query,
                                          language=Config['language'],
                                          adult=adult)
                
                # paged results, so retrieve them all (max_results)
                results = []
                for i, result in enumerate(search_results):
                    log.debug("Search-Result: %s" % result)
                    results.append(result)
                    if i >= max_results:
                        break
                
            except URLError as e:
                raise DataRetrievalError(
                        "Error connecting to themoviedb.com: %s" % e)

#            if len(results) == 0:
#                raise ShowNotFound(
#                        "Movie '%s' not found on themoviedb.com"
#                            % ' '.join(query.split('+')))
            
            try:
                return self.__selector.select(force_name or self.movietitle,
                                          results,
                                          candidate_name=operator.attrgetter("title"))
            except MatchingDataNotFound:
                raise ShowNotFound(
                        "Movie '%s' not found on themoviedb.com"
                            % ' '.join(query.split('+')))

        if uid is not None:
            # Search By UID
            try:
                req = tmdb3.utils.Request("movie/{0}".format(int(uid)),
                                          include_adult=adult)
                movie = tmdb3.utils.MovieSearchResult(req,
                               language=Config['language'])[0]
            except URLError as e:
                raise DataRetrievalError(
                            "Error connecting to themoviedb.com: %s" % e)
            except IndexError:
                raise ShowNotFound("Movie #%d not found on themoviedb.com" % uid)

        else:
            queryend = "+%d" % self.releasedate if self.releasedate else ""

            query = "%s%s" % (force_name or self.movietitle, queryend)
            movie = searchMovie(query)

        #log.debug("Found Series\n\t" + '\n\t'.join((
        #        "%s: %s" % (attr, getattr(movie, attr))
        #            for attr in dir(movie) if attr[0] != '_')))
        # use corrected series name
        self.movietitle = makeValidFilename(replaceOutputName(movie.title))
        self.releasedate = release_date(movie)

        self.genres = format_genres(g.name for g in movie.genres)
        self.userrating = movie.userrating
        self.id = movie.id

    def _init_from_match(self, match):
        groups = match.groupdict()
        groups.pop("rdsep", None)
        groups.pop("rsep", None)

        if 'movietitle' not in groups:
            raise InvalidMatch(
                            "Regex must contain movietitle. Pattern was:\n"
                            + match.re.pattern)
        elif Config['force_name']:
            movietitle = Config['force_name']
        elif groups['movietitle'] is None:
            raise ConfigValueError("Regex match error: movietitle=None in %s"
                                   % match.re.pattern)
        else:
            movietitle = groups.get('movietitle', None)

        movietitle = cleanRegexedName(movietitle)
        movietitle = replaceInputName(movietitle)
        groups['movietitle'] = movietitle

        extra = groups.pop("extra", None)

        if extra:
            # extract part: ie Cd 1, Disc2, dvd one, etcc
            extramatch = re.match(
                "(?i).*"
                "(part|disc|cd|dvd)"
                r"[ \.+\-_]?"
                r"([0-9]+|(?:" + TextToNumber.pattern + r"[ \.+\-_]?)+)"
                ".*",
                extra)
            if extramatch:
                label, number = extramatch.groups()
                try:
                    number = TextToNumber(number.strip().split())
                except KeyError:
                    pass
                groups['part'] = " ".join(("Part", number)).title()

            if groups.get("resolution", None) is None:
                # we try to put resolution guess in
                ripsrc = re.match("(?i).*"
                                  r"(b[rd]rip|bluray|dvd[ \.+\-_]?(rip)?)"
                                  ".*",
                                  extra)
                vcodec = re.match("(?i).*"
                                  "([hx]264|xvid|divx|theora|webm)"
                                  ".*",
                                  extra)
                if ripsrc:
                    ripsrc = ripsrc.groups()[0].lower()
                if vcodec:
                    vcodec = vcodec.groups()[0].lower()

                hd = vcodec in ("h264", "x264")

                if ripsrc == "bluray" and hd:
                    groups['resolution'] = "1080p"

                elif ripsrc in ("brrip", "bdrip") and hd:
                    groups['resolution'] = "720p"

                #info("GUESS-RES: ripsrc={0} vcodec={1}",ripsrc.groups)(, vcodec)

            groups['tags'] = [tag.lower() for tag in
                    re.split(r"[ \.+\-_{}\(\)\[\]]", extra.strip())
                               if len(tag)]

            if groups.get('resolution', None):
                groups['tags'].append(groups['resolution'])

        log.debug("%s\n" % match.string
             + '\n'.join(('{0:>30} :   {1}'.format(k,str(v))
                          for k, v in groups.iteritems() if v))
             + "\n")

        self.extra = groups
        self.movietitle = movietitle
        self.part = groups.get("part", None)
        self.resolution = groups.get("resolution", None)

        try:
            self.releasedate = int(groups.get("releasedate", None))
        except TypeError:
            self.releasedate = None
