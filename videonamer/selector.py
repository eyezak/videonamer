#!/usr/bin/env python

"""Utilities for tvnamer, including filename parsing
"""
__all__ = ('Selector', 'ConsoleSelector', )

import logging
import operator
import difflib

from config import Config
from tvnamer_exceptions import UserAbort, MatchingDataNotFound

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)

class Selector(object):

    def __init__(self):
        self.__history = {}

    @classmethod
    def ratio_map(cls, name, candidates, candidate_name=lambda x: str(x),
                  junk_chars=" \t:-=_\\/,.'\"?"):
        matcher = difflib.SequenceMatcher(lambda (x): x in junk_chars,
                                          name.lower(),
                                          "")
        for candidate in candidates:
            matcher.set_seq2(candidate_name(candidate).lower())
            yield candidate, matcher.quick_ratio()

    def select(self, name, candidates, candidate_name=lambda x: str(x),
                     fuzz_ratio=0.25, min_ratio=0.65):
        if len(candidates) == 0:
            raise MatchingDataNotFound(name)

        last_candidate = self.__history.get(name, None)
        if last_candidate and last_candidate in candidates:
            # Previous choice for this name is valid, return it!
            return last_candidate

        ratiomap = sorted(self.ratio_map(name, candidates, candidate_name),
                      key=operator.itemgetter(1),
                      reverse=True)

        minratio = max(ratiomap[0][1] - fuzz_ratio, min_ratio)
        log.debug("Minimum-Ratio: %d" % (minratio * 100))
        ratiomap_mini = [ (c, r) for c, r in ratiomap if r > minratio ]
        
        if len(ratiomap_mini) == 0:
            raise MatchingDataNotFound(name)
        
        if len(ratiomap_mini) == 1 or Config['select_first']:
            # Single result / select_first, return it!
            log.debug("Automatically selecting %s result (%d%%)"
                  % ("only good" if len(ratiomap_mini) == 1 else "best-match",
                     ratiomap_mini[0][1]))
            candidate = ratiomap_mini[0][0]
        else:
            # Chain down to child class to do real selection        
            candidate = self.do_select(name, ratiomap_mini, candidate_name)
        
        self.__history[name] = candidate
        return candidate

    def do_select (self, name, ratiomap, candidate_name):
        log.info("Automatically returning best-match search result")
        return ratiomap[0][0]

class ConsoleSelector(Selector):
    
    def __init__(self, candidate_formatter=lambda x: str(x)):
        super(ConsoleSelector, self).__init__()
        # Highlight default option with [ ]
        self.candidate_formatter = candidate_formatter

    def _displaySeries(self, name, ratiomap):
        """Helper function, lists series with corresponding ID
        """
        print "Search Results for %s:" % name
        #print " #   Rating  " + "Result" + " "*36 + "Id #"
        for i, (candidate, ratio) in enumerate(ratiomap):
            i_show = i + 1 # Start at more human readable number 1 (not 0)
            log.debug('Showing candidates[%s], candidate %s)' 
                      % (i, candidate))
            
            print "%2d) %3d%%:   %-50s  #%05d" % (
                i_show,
                ratio * 100,
                self.candidate_formatter(candidate),
                #cshow['language'].encode("UTF-8", "ignore"),
                candidate.id
            )

    def do_select(self, name, ratiomap, candidate_name):
        self._displaySeries(name, ratiomap)

        while True: # return breaks this loop
            try:
                print "Enter choice (1-%d, q to quit, ? for help):" % len(ratiomap), 
                choice = raw_input()
            except KeyboardInterrupt:
                raise UserAbort("User aborted (^c keyboard interupt)")
            except EOFError:
                raise UserAbort("User aborted (EOF received)")

            log.debug('Got choice of: %s' % (choice))
            try:
                selected_id = int(choice) - 1 # The human entered 1 as first result, not zero
            except ValueError: # Input was not number
                if choice == "q":
                    log.debug('Got quit command (q)')
                    raise UserAbort("User aborted ('q' quit command)")
                elif choice == "?":
                    print "## Help"
                    print "# Enter the number that corresponds to the correct show."
                    print "# ? - this help"
                    print "# q - abort tvnamer"
                else:
                    log.debug('Unknown keypress %s' % (choice))
            else:
                log.debug('Trying to return ID: %d' % (selected_id))
                try:
                    return ratiomap[selected_id][0]
                except IndexError:
                    log.error('Invalid show number entered!')
                    #print "Invalid number (%s) selected!"
                    #self._displaySeries(allSeries)
