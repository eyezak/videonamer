#!/usr/bin/env python

"""Holds default config values
"""

defaults = {
    # Media type: tv or movie
    'media_type': 'tv',

    # Select first series search result
    'select_first': False,
    
    # Maximum results to return for a search (passed to fuzzy-matcher)
    'max_results': 15,

    # Always rename files
    'always_rename': False,

    # Batch (same as select_first and always_rename)
    'batch': False,
    
    'test_mode': False,

    # Fail if error finding show data (thetvdb.com is down etc)
    # Only functions when always_rename is True
    'skip_file_on_error': True,

    # Forcefully overwrite existing files when renaming or
    # moving. This potentially destroys the old file. Default is False
    'overwrite_destination_on_rename': False,
    'overwrite_destination_on_move': False,

    # Verbose mode (debugging info)
    'verbose': False,

    # Recurse more than one level into folders. When False, only
    # desends one level.
    'recursive': False,
    
    # Library mode means directories are renamed like normal arguments
    'library': False,
    
    # Library blacklist (for tv shows mostly)
    'library_blacklist': [{ "is_regex": True, "match": "(?i)^(sample|subtitles|(part|disc|cd|dvd|bluray|season)[ \.+\-_]?[0-9]+)$" },],

    # When non-empty, only look for files with this extension.
    # No leading dot, for example: ['avi', 'mkv', 'mp4']
    'valid_extensions': [],

    # When non-empty, filter out filenames that match these expressions. Either simple
    # matches or regexs can be used. The following are near enough equivalent:
    # [{"is_regex": true, "match": ".*sample.*"}, {"is_regex": false, "match": "sample"}]
    'filename_blacklist': [{ "is_regex": True, "match": 
        "(?i)^(sample|english|french|dutch|german|italian|portuguese|portuguese-brazil|spanish|.*(cd|dvd|disc|case)[ \.+\-_]cover)$"
    },],

    # Force Windows safe filenames (always True on Windows)
    'windows_safe_filenames': False,

    # Replace accented unicode characters with ASCII equivalents,
    # removing characters than can't be translated.
    'normalize_unicode_filenames': False,

    # Convert output filenames to lower case (applied after replacements)
    'lowercase_filename': False,

    # Extra characters to consider invalid in output filenames (which are
    # replaced by the character in replace_invalid_characters_with)
    'custom_filename_character_blacklist': '',

    # Replacement characters for invalid filename characters
    'replace_invalid_characters_with': '',

    # Replacements performed on input file before parsing.
    'input_filename_replacements': [
    ],

    # Replacements performed on files after the new name is generated.
    'output_filename_replacements': [
    ],

    # Replacements are performed on the full path used by move_files feature,
    # including the filename
    'move_files_fullpath_replacements': [
    ],

    # Language to (try) and retrieve episode data in
    'language': 'en',

    # Search in all possible languages
    'search_all_languages': True,

    # Move renamed files to directory?
    'move_files_enable': False,

    # If true, convert the variable/dynamic parts of the destination
    # to lower case. Does not affect the static parts; for example,
    # if move_files_destination is set to
    # '/Foo/Bar/%(seriesname)s/Season %(seasonnumber)d'
    # then only the series name will be converted to lower case.
    'move_files_lowercase_destination': False,

    # Destination to move files to. Trailing slash is not necessary.
    # Use forward slashes, even on Windows. Realtive paths are realtive to
    # the existing file's path (not current working dir). A value of '.' will
    # not move the file anywhere.

    'tv_destination': '.',
    'movie_destination': '.',

    # Use Python's string formatting to add dynamic paths. Available variables:
    # - %(seriesname)s
    # - %(seasonnumber)d
    # - %(episodenumbers)s (Note: this is a string, formatted with config
    #                       variable episode_single and joined with episode_separator)
    'tv_dirname': '%(seriesname)s/Season %(seasonnumber)d',

    # Use Python's string formatting to add dynamic paths. Available variables:
    # - %(seriesname)s
    # - %(year)s
    # - %(month)s
    # - %(day)s
    'tv_dirname_date': '%(seriesname)s/%(year)s',

    # Use Python's string formatting to add dynamic paths. Available variables:
    # - %(movietitle)s
    # - %(releasedate)d
    # - %(resolution)s 
    'movie_dirname': '%(movietitle)s (%(releasedate)d)',

    # Force the move-files feature to always move the file.
    #
    # If False, when a file is moved between partitions (or from a
    # network volume), the original is left untouched (i.e it is
    # copied).  If True, this will delete the file from the original
    # volume, after the copy has complete.
    'always_move': False,
    
    # Allow user to copy files to specified move location without renaming files.
    'move_files_only': False,
    

    # Patterns to parse input filenames with
    'tv_patterns': [
        # [group] Show - 01-02 [crc]
        '''^\[(?P<group>.+?)\][ ]?               # group name, captured for [#100]
        (?P<seriesname>.*?)[ ]?[-_][ ]?          # show name, padding, spaces?
        (?P<episodenumberstart>\d+)              # first episode number
        ([-_]\d+)*                               # optional repeating episodes
        [-_](?P<episodenumberend>\d+)            # last episode number
        (?=                                      # Optional group for crc value (non-capturing)
          .*                                     # padding
          \[(?P<crc>.+?)\]                       # CRC value
        )?                                       # End optional crc group
        [^\/]*$''',

        # [group] Show - 01 [crc]
        '''^\[(?P<group>.+?)\][ ]?               # group name, captured for [#100]
        (?P<seriesname>.*)                       # show name
        [ ]?[-_][ ]?                             # padding and seperator
        (?P<episodenumber>\d+)                   # episode number
        (?=                                      # Optional group for crc value (non-capturing)
          .*                                     # padding
          \[(?P<crc>.+?)\]                       # CRC value
        )?                                       # End optional crc group
        [^\/]*$''',

        # foo s01e23 s01e24 s01e25 *
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Ss](?P<seasonnumber>[0-9]+)             # s01
        [\.\- ]?                                 # separator
        [Ee](?P<episodenumberstart>[0-9]+)       # first e23
        ([\.\- ]+                                # separator
        [Ss](?P=seasonnumber)                    # s01
        [\.\- ]?                                 # separator
        [Ee][0-9]+)*                             # e24 etc (middle groups)
        ([\.\- ]+                                # separator
        [Ss](?P=seasonnumber)                    # last s01
        [\.\- ]?                                 # separator
        [Ee](?P<episodenumberend>[0-9]+))        # final episode number
        [^\/]*$''',

        # foo.s01e23e24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Ss](?P<seasonnumber>[0-9]+)             # s01
        [\.\- ]?                                 # separator
        [Ee](?P<episodenumberstart>[0-9]+)       # first e23
        ([\.\- ]?                                # separator
        [Ee][0-9]+)*                             # e24e25 etc
        [\.\- ]?[Ee](?P<episodenumberend>[0-9]+) # final episode num
        [^\/]*$''',

        # foo.1x23 1x24 1x25
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?P<seasonnumber>[0-9]+)                 # first season number (1)
        [xX](?P<episodenumberstart>[0-9]+)       # first episode (x23)
        ([ \._\-]+                               # separator
        (?P=seasonnumber)                        # more season numbers (1)
        [xX][0-9]+)*                             # more episode numbers (x24)
        ([ \._\-]+                               # separator
        (?P=seasonnumber)                        # last season number (1)
        [xX](?P<episodenumberend>[0-9]+))        # last episode number (x25)
        [^\/]*$''',

        # foo.1x23x24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?P<seasonnumber>[0-9]+)                 # 1
        [xX](?P<episodenumberstart>[0-9]+)       # first x23
        ([xX][0-9]+)*                            # x24x25 etc
        [xX](?P<episodenumberend>[0-9]+)         # final episode num
        [^\/]*$''',

        # foo.s01e23-24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Ss](?P<seasonnumber>[0-9]+)             # s01
        [\.\- ]?                                 # separator
        [Ee](?P<episodenumberstart>[0-9]+)       # first e23
        (                                        # -24 etc
             [\-]
             [Ee]?[0-9]+
        )*
             [\-]                                # separator
             [Ee]?(?P<episodenumberend>[0-9]+)   # final episode num
        [\.\- ]                                  # must have a separator (prevents s01e01-720p from being 720 episodes)
        [^\/]*$''',

        # foo.1x23-24*
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?P<seasonnumber>[0-9]+)                 # 1
        [xX](?P<episodenumberstart>[0-9]+)       # first x23
        (                                        # -24 etc
             [\-+][0-9]+
        )*
             [\-+]                               # separator
             (?P<episodenumberend>[0-9]+)        # final episode num
        ([\.\-+ ].*                              # must have a separator (prevents 1x01-720p from being 720 episodes)
        |
        $)''',

        # foo.[1x09-11]*
        '''^(?P<seriesname>.+?)[ \._\-]          # show name and padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        \[                                       # [
            ?(?P<seasonnumber>[0-9]+)            # season
        [xX]                                     # x
            (?P<episodenumberstart>[0-9]+)       # episode
            ([\-+] [0-9]+)*
        [\-+]                                    # -
            (?P<episodenumberend>[0-9]+)         # episode
        \]                                       # \]
        [^\\/]*$''',

        # foo - [012]
        '''^((?P<seriesname>.+?)[ \._\-])?       # show name and padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        \[                                       # [ not optional (or too ambigious)
        (?P<episodenumber>[0-9]+)                # episode
        \]                                       # ]
        [^\\/]*$''',
        # foo.s0101, foo.0201
        '''^(?P<seriesname>.+?)[ \._\-]
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ \._\-])?
        [Ss](?P<seasonnumber>[0-9]{{2}})
        [\.\- ]?
        (?P<episodenumber>[0-9]{{2}})
        [^0-9]*$''',

        # foo.1x09*
        '''^((?P<seriesname>.+?)[ \._\-])?       # show name and padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        \[?                                      # [ optional
        (?P<seasonnumber>[0-9]+)                 # season
        [xX]                                     # x
        (?P<episodenumber>[0-9]+)                # episode
        \]?                                      # ] optional
        [^\\/]*$''',

        # foo.s01.e01, foo.s01_e01, "foo.s01 - e01"
        '''^((?P<seriesname>.+?)[ \._\-])?
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        \[?
        [Ss](?P<seasonnumber>[0-9]+)[ ]?[\._\- ]?[ ]?
        [Ee]?(?P<episodenumber>[0-9]+)
        \]?
        [^\\/]*$''',

        # foo.2010.01.02.etc
        '''
        ^((?P<seriesname>.+?)[ \._\-])?          # show name
        (?P<year>\d{{4}})                          # year
        [ \._\-]                                 # separator
        (?P<month>\d{{2}})                         # month
        [ \._\-]                                 # separator
        (?P<day>\d{{2}})                           # day
        [^\/]*$''',

        # foo - [01.09]
        '''^((?P<seriesname>.+?))                # show name
        [ \._\-]?                                # padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        \[                                       # [
        (?P<seasonnumber>[0-9]+?)                # season
        [.]                                      # .
        (?P<episodenumber>[0-9]+?)               # episode
        \]                                       # ]
        [ \._\-]?                                # padding
        [^\\/]*$''',

        # Foo - S2 E 02 - etc
        '''^(?P<seriesname>.+?)[ ]?[ \._\-][ ]?
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Ss](?P<seasonnumber>[0-9]+)[\.\- ]?
        [Ee]?[ ]?(?P<episodenumber>[0-9]+)
        [^\\/]*$''',

        # Show - Episode 9999 [S 12 - Ep 131] - etc
        '''

        (?P<seriesname>.+)                       # Showname
        [ ]-[ ]                                  # -
        [Ee]pisode[ ]\d+                         # Episode 1234 (ignored)
        [ ]
        \[                                       # [
        [sS][ ]?(?P<seasonnumber>\d+)            # s 12
        ([ ]|[ ]-[ ]|-)                          # space, or -
        ([eE]|[eE]p)[ ]?(?P<episodenumber>\d+)   # e or ep 12
        \]                                       # ]
        .*$                                      # rest of file
        ''',

        # show name 2 of 6 - blah
        '''^(?P<seriesname>.+?)                  # Show name
        [ \._\-]                                 # Padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?P<episodenumber>[0-9]+)                # 2
        of                                       # of
        [ \._\-]?                                # Padding
        \d+                                      # 6
        ([\._ -]|$|[^\\/]*$)                     # More padding, then anything
        ''',

        # Show.Name.Part.1.and.Part.2
        '''^(?i)
        (?P<seriesname>.+?)                        # Show name
        [ \._\-]                                   # Padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?:part|pt)?[\._ -]
        (?P<episodenumberstart>[0-9]+)             # Part 1
        (?:
          [ \._-](?:and|&|to)                        # and
          [ \._-](?:part|pt)?                        # Part 2
          [ \._-](?:[0-9]+))*                        # (middle group, optional, repeating)
        [ \._-](?:and|&|to)                        # and
        [ \._-]?(?:part|pt)?                       # Part 3
        [ \._-](?P<episodenumberend>[0-9]+)        # last episode number, save it
        [\._ -][^\\/]*$                            # More padding, then anything
        ''',

        # Show.Name.Part1
        '''^(?P<seriesname>.+?)                  # Show name\n
        [ \\._\\-]                               # Padding\n
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Pp]art[ ](?P<episodenumber>[0-9]+)      # Part 1\n
        [\\._ -][^\\/]*$                         # More padding, then anything\n
        ''',

        # show name Season 01 Episode 20
        '''^(?P<seriesname>.+?)[ ]?               # Show name
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Ss]eason[ ]?(?P<seasonnumber>[0-9]+)[ ]? # Season 1
        [Ee]pisode[ ]?(?P<episodenumber>[0-9]+)   # Episode 20
        [^\\/]*$''',                              # Anything

        # foo.103*
        '''^(?P<seriesname>.+)[ \._\-]
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?P<seasonnumber>[0-9]{{1,2}})
        (?P<episodenumber>[0-9]{{2}})
        (?:[\._ -][^\\/]*)?$''',

        # foo.0103*
        '''^(?P<seriesname>.+)[ \._\-]
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        (?P<seasonnumber>[0-9]{{2}})
        (?P<episodenumber>[0-9]{{2,3}})
        [\._ -][^\\/]*$''',

        # show.name.e123.abc
        '''^(?P<seriesname>.+?)                  # Show name
        [ \._\-]                                 # Padding
        (?:[\[\(]?(?P<year>[0-9]{{4}})[\]\)]?[ ]?[ \._\-][ ]?)?
        [Ee](?P<episodenumber>[0-9]+)            # E123
        [\._ -][^\\/]*$                          # More padding, then anything
        ''',
    ],

    # Patterns to parse input files for movies
    "movie_patterns": [
	    '''^(?i)
	    (?P<movietitle>.+)                                        # movie title
	    (?:{gen_sep}?(?P<rdsep>[\(\[])|{gen_sep})                   # padding
	    (?P<releasedate>(?:20(?:0[0-9]|1[0-3])|1[0-9]{{3}}))          # releasedate
	    (?(rdsep)[\)\]]{gen_sep}?|{gen_sep})                               # padding
	    (?P<rsep>[\(\[])?                                         # padding
	    (?P<resolution>(?:240|320|480|576|720|1080|2304|2160)[ip])  # resolution
	    (?(rsep)[\)\]]{gen_sep}?|{gen_sep})                                           # padding
	    (?P<extra>.*)$                                  # extra
	    ''',

	    '''^(?i)
	    {movietitle}                               # movie title
	    (?:{gen_sep}?(?P<rdsep>[\(\[])|{gen_sep})       # padding
	    {releasedate}          # releasedate
	    (?(rdsep)[\)\]]{gen_sep}?|{gen_sep})                                          # padding
	    (?P<extra>.*)$                                  # extra
	    ''',

	    '''^(?i)
	    (?P<movietitle>(?:.(?!unrated|special[ \.+\-_]edition|director'?s[ \.+\-_]cut))+)
	    ([ \.+\-_]
	    (?P<releasetype>unrated|special[ \.+\-_]edition|director'?s[ \.+\-_]cut))?
	    [ \.+\-_]
	    (?P<rsep>[\(\[])?
	    (?P<resolution>(?:240|320|480|576|720|1080|2304|2160)[ip])
	    (?(rsep)[\(\]])
	    (?P<extra>[ \.+\-_]?.*)$
	    ''',

	    '''^(?i)
	    (?P<movietitle>.+)
	    (?:(?P<releasedate>(?:20(?:0[0-9]|1[0-3])|1[0-9]{{3}}))|
	    (?P<resolution>(?:240|320|480|576|720|1080|2304|2160)[ip]))$
	    ''',

	    '''^(?i)
	    (?P<movietitle>.+?)
	    (?P<extra>[ \.+\-_]
	    (?:bluray|[Bb][RrDd][Rr][Ii][Pp]|[Dd][Vv][Dd][ \\.+\\-_]?[Rr][Ii][Pp]|[hHxX]264|[Xx][Vv][Ii][Dd]|[Dd][Ii][Vv][Xx]|cd[0-9]+|[Uu][Nn][Rr][Aa][Tt][Ee][Dd]).*)*$
	    '''
	], 


    # Common regexes
    'common_patterns': {
        'gen_sep': '[ ]*[\.+\-_ ][ ]*',
        'li_sep' : '[ ]*[-_][ ]*',
        'res': '(?:240|320|480|576|720|1080|2304|2160|4096)[ip]',
        'date': '(?:20(?:0[0-9]|1[0-3])|1[0-9]{3})',
        'edition': '(?:unrated|special[ ]*[ \.+\-_][ ]*edition|director[\'`]?s[ \.+\-_]cut)',
        'releasedate': '(?P<releasedate>(?:20(?:0[0-9]|1[0-3])|1[0-9]{{3}}))',
        'movietitle': '(?P<movietitle>[^[({]+)'
    },


    # Formats for renamed files. Variations for with/without episode,
    # and with/without season number.
    'tv_filename_with_episode':
     '%(seriesname)s - [%(seasonnumber)02dx%(episode)s] - %(episodetitle)s%(extension)s',
    'tv_filename_without_episode':
     '%(seriesname)s - [%(seasonnumber)02dx%(episode)s]%(extension)s',

    # Seasonless filenames.
    'tv_filename_with_episode_no_season':
      '%(seriesname)s - [%(episode)s] - %(episodetitle)s%(extension)s',
    'tv_filename_without_episode_no_season':
     '%(seriesname)s - [%(episode)s]%(extension)s',

    # Date based filenames.
    # Series - [2012-01-24] - Ep name.ext
    'tv_filename_with_date_and_episode':
     '%(seriesname)s - [%(episode)s] - %(episodetitle)s%(extension)s',
    'tv_filename_with_date_without_episode':
     '%(seriesname)s - [%(episode)s]%(extension)s',

    # Anime filenames.
    # [AGroup] Series - 02 - Some Ep Name [CRC1234].ext
    # [AGroup] Series - 02 [CRC1234].ext
    'tv_filename_anime_with_episode':
     '[%(group)s] %(seriesname)s - %(episode)s - %(episodetitle)s [%(crc)s]%(extension)s',

    'tv_filename_anime_without_episode':
     '[%(group)s] %(seriesname)s - %(episode)s [%(crc)s]%(extension)s',

    # Same, without CRC value
    'tv_filename_anime_with_episode_without_crc':
     '[%(group)s] %(seriesname)s - %(episode)s - %(episodetitle)s%(extension)s',

    'tv_filename_anime_without_episode_without_crc':
     '[%(group)s] %(seriesname)s - %(episode)s%(extension)s',


    # Movie Filename
    'movie_filename_resolution':
     '%(movietitle)s (%(releasedate)s) [%(resolution)s]%(extension)s',
    
    'movie_filename':
     '%(movietitle)s (%(releasedate)s)%(extension)s',

    'movie_filename_resolution_part':
     '%(movietitle)s (%(releasedate)s) [%(resolution)s] %(part)s%(extension)s',
    
    'movie_filename_part':
     '%(movietitle)s (%(releasedate)s) %(part)s%(extension)s',

    # Used to join multiple episode names together
    'multiep_join_name_with': ', ',

    # Format for numbers (python string format), %02d does 2-digit
    # padding, %d will cause no padding
    'episode_single': '%02d',

    # String to join multiple number
    'episode_separator': ',',
    
    'genre_single': '%s',
    'genre_separator': ',',
    
    # force tmdb/tvdb ID to use instead of searching if the value is set
    'force_id': None,
    
    # Forced Name to use
    'forced_name': None,
    
    # replace series names before/after passing to TVDB
    # input replacements are regular expressions for the series as parsed from
    # filenames, for instance adding or removing the year, or expanding abbreviations
    'input_name_replacements': {},
    
    # output replacements are for transforms of the TVDB series names
    # since these are perfectly predictable, they are simple strings
    # not regular expressions
    'output_name_replacements': {},

}
