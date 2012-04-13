#!/usr/bin/env python

"""Utilities for tvnamer, including filename parsing
"""
__all__ = ('TvInfo',)

import os, os.path
import operator
import re
import logging
import datetime

from tvdb_api import (Tvdb, BaseUI,
                      tvdb_error,
                      tvdb_shownotfound,
                      tvdb_userabort,
                      tvdb_episodenotfound,
                      tvdb_seasonnotfound,
                      tvdb_attributenotfound)

from config import Config
from utils import (replaceOutputName,
                   cleanRegexedName,
                   replaceInputName,
                   makeValidFilename,
                   TextToNumber,
                   formatEpisodeName,
                   formatEpisodeNumbers,
                   handleYear)
from tvnamer_exceptions import (ShowNotFound, EpisodeNotFound,
                                SeasonNotFound, EpisodeNameNotFound,
                                DataRetrievalError,
                                ConfigValueError, InvalidMatch,
                                UserAbort,
                                MatchingDataNotFound)
from info import BaseInfo
from selector import ConsoleSelector

log = logging.getLogger(__name__)

def tv_formatter(tv):
    return "{0} ({1})".format(tv.title.encode("UTF-8", "ignore"),
                              release_date(tv))

class TvdbSelector(BaseUI):
    
    __selector = ConsoleSelector(candidate_formatter=tv_formatter)
    
    def set_name(self, name):
        self.name = name
    
    def selectSeries(self, candidates):
        return self.__selector.select(self.name, 
                                      candidates,
                                      candidate_name=tv_formatter)


def format_genres( genres):
    """Format episode genre(s) into string, using configured values
    """
    return Config['genre_separator'].join(
            Config['genre_single'] % g for g in genres)

class TvInfo(BaseInfo):
    """Stores information (tvtitle), and contains
    logic to generate new name
    """
    
    _media_type = 'tv'
    _destination_key = 'tv_destination'
    _dirname_key = 'tv_dirname'
    _unique_attrs = ('seriesname', 'seasonnumber', 'episodenumbers')
    _parser_key = 'tv_patterns'

    __tvdb_instance = Tvdb()
    __selector = TvdbSelector(__tvdb_instance.config)


    def set_episodenumbers(self, episodenumbers):
        self.episodenumbers = episodenumbers
        if self.date_based:
            self.episode = str(episodenumbers[0])
        else:
            self.episode = formatEpisodeNumbers(self.episodenumbers)

    def set_episodename(self, episodename):
        self.episodename = episodename
        if isinstance(self.episodename, list):
                self.episodetitle = formatEpisodeName(
                    self.episodename,
                    join_with = Config['multiep_join_name_with']
                )
        else:
            self.episodetitle = episodename

    def _filename_key(self):
        if self.date_based:
            return 'tv_filename_with_date_%s_episode' % (
                            'and' if self.episodename else 'without')
        
        config_key = 'tv_filename_%s_episode' % (
                        'with' if self.episodename else 'without')
        if self.seasonnumber is None:
            config_key = '_'.join(config_key, 'no_season')
        
        return config_key

    def populate_from_db(self, force_name=None, uid=None, adult=False):
        """Queries the tvdb_api
        If series cannot be found, it will warn the user. If the episode is not
        found, it will use the corrected show name and not set an episode name.
        If the site is unreachable, it will warn the user. If the user aborts
        it will catch tvdb_api's user abort error and raise tvnamer's
        """
        def find_show(name, uid=None):
            self.__selector.set_name(force_name or name)
            try:
                if uid is None:
                    show = self.__tvdb_instance[force_name or name]
                else:
                    uid = int(uid)
                    self.__tvdb_instance._getShowData(uid, Config['language'])
                    show = self.__tvdb_instance[uid]
            except tvdb_error, errormsg:
                raise DataRetrievalError("Error contacting thetvdb.com: %s" %
                                          errormsg)
            except (tvdb_shownotfound, MatchingDataNotFound):
                # No such series found.
                raise ShowNotFound("Show %s not found on thetvdb.com" % name)
            except tvdb_userabort, error:
                raise UserAbort(unicode(error))
            else:
                return show
        
        if self.__tvdb_instance is None:
            # cache tvdb instance in class, but wait until 1st call
            self.__class__.__tvdb_instance = Tvdb(
                    interactive = not Config['select_first'],
                    search_all_languages = Config['search_all_languages'],
                    language = Config['language'])
        
        year_in_query = (uid is None and 
                         not self.date_based and 
                         getattr(self, 'year', None) is not None)
        if year_in_query:
            name = '%s (%s)' % (self.seriesname, self.year)
        else:
            name = self.seriesname
        try:
            show = find_show(name, uid=uid)
        except ShowNotFound:
            if year_in_query:
                name = self.seriesname
                show = find_show(name, uid=uid)
            else:
                raise
        # Series was found, use corrected series name
        self.seriesname = show['seriesname']

        if self.date_based:
            # Date-based episode
            epnames = []
            for cepno in self.episodenumbers:
                try:
                    sr = show.airedOn(cepno)
                    if len(sr) > 1:
                        raise EpisodeNotFound(
                            "Ambigious air date %s, there were %s episodes on that day" % (
                            cepno, len(sr)))
                    epnames.append(sr[0]['episodename'])
                except tvdb_episodenotfound:
                    raise EpisodeNotFound(
                        "Episode that aired on %s could not be found" % (
                        cepno))
            self.set_episodename(epnames)
            return

        if not hasattr(self, "seasonnumber") or self.seasonnumber is None:
            # Series without concept of seasons have all episodes in season 1
            seasonnumber = 1
        else:
            seasonnumber = self.seasonnumber

        epnames = []
        for cepno in self.episodenumbers:
            try:
                episodeinfo = show[seasonnumber][cepno]

            except tvdb_seasonnotfound:
                raise SeasonNotFound(
                    "Season %s of show %s could not be found" % (
                    seasonnumber,
                    name))

            except tvdb_episodenotfound:
                # Try to search by absolute_number
                sr = show.search(cepno, "absolute_number")
                if len(sr) > 1:
                    # For multiple results try and make sure there is a direct match
                    unsure = True
                    for e in sr:
                        if int(e['absolute_number']) == cepno:
                            epnames.append(e['episodename'])
                            unsure = False
                    # If unsure error out            
                    if unsure:
                        raise EpisodeNotFound(
                            "No episode actually matches %s, found %s results instead" % (cepno, len(sr)))
                elif len(sr) == 1:
                    epnames.append(sr[0]['episodename'])
                else:
                    raise EpisodeNotFound(
                        "Episode %s of show %s, season %s could not be found (also tried searching by absolute episode number)" % (
                            cepno,
                            name,
                            seasonnumber))

            except tvdb_attributenotfound:
                raise EpisodeNameNotFound(
                    "Could not find episode name for %s" % cepno)
            else:
                epnames.append(episodeinfo['episodename'])

        self.set_episodename(epnames)

    def _init_from_match(self, match):   
        namedgroups = match.groupdict()

        self.date_based = False
        try:
            self.seasonnumber = int(namedgroups['seasonnumber'])
        except (KeyError, TypeError):
            self.seasonnumber = None

        seriesname = namedgroups.get('seriesname', None)
        if seriesname is None:
            raise ConfigValueError(
                "Regex must contain seriesname. Pattern was:\n" + match.pattern)
        seriesname = cleanRegexedName(seriesname)
        self.seriesname = replaceInputName(seriesname)

        if namedgroups.get('year', None) and not 'month' in namedgroups:
            self.year = int(namedgroups['year'])

        if 'episodenumber1' in namedgroups:
            # Multiple episodes, have episodenumber1 or 2 etc
            epnos = []
            for cur in namedgroups:
                epnomatch = re.match('episodenumber(\d+)', cur)
                if epnomatch:
                    epnos.append(int(match.group(cur)))
            epnos.sort()
            episodenumbers = epnos

        elif 'episodenumberstart' in namedgroups:
            # Multiple episodes, regex specifies start and end number
            start = int(namedgroups['episodenumberstart'])
            end = int(namedgroups['episodenumberend'])
            if start > end:
                # Swap start and end
                start, end = end, start
            episodenumbers = range(start, end + 1)

        elif 'episodenumber' in namedgroups:
            episodenumbers = [int(namedgroups['episodenumber']), ]

        elif 'year' in namedgroups and 'month' in namedgroups and 'day' in namedgroups:
            year = handleYear(namedgroups['year'])

            episodenumbers = [datetime.date(year,
                                            int(namedgroups['month']),
                                            int(namedgroups['day']))]
            self.date_based = True
        else:
            raise ConfigValueError(
                "Regex does not contain episode number group, should"
                "contain episodenumber, episodenumber1-9, or"
                "episodenumberstart and episodenumberend\n\nPattern"
                "was:\n" + match.pattern)
        
        self.set_episodenumbers(episodenumbers)
