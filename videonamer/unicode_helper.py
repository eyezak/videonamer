#!/usr/bin/env python

"""Helpers to deal with strings, unicode objects and terminal output
"""

import sys

def unicodify(obj, encoding = "utf-8"):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    else:
        try:
            iter(obj)
        except TypeError:
            pass
        else:
            obj = type(obj)((unicodify(item, encoding=encoding) for item in obj))
    return obj

def unidecodify(obj):
    if isinstance(obj, basestring):
        if not isinstance(obj, str):
            obj = obj.__str__()
    else:
        try:
            iter(obj)
        except TypeError:
            pass
        else:
            obj = type(obj)((unidecodify(item) for item in obj))
    return obj


def _p(*args, **kw):
    """Rough implementation of the Python 3 print function,
    http://www.python.org/dev/peps/pep-3105/

    def print(*args, sep=' ', end='\n', file=None)

    """
    kw.setdefault('encoding', 'utf-8')
    kw.setdefault('sep', ' ')
    kw.setdefault('end', '\n')

    new_args = []
    for x in args:
        if not isinstance(x, basestring):
            new_args.append(repr(x))
        else:
            if kw['encoding'] is not None:
                new_args.append(x.encode(kw['encoding']))
            else:
                new_args.append(x)

    return kw['sep'].join(new_args) + kw['end']


def p(*args, **kw):
    """Rough implementation of the Python 3 print function,
    http://www.python.org/dev/peps/pep-3105/

    def print(*args, sep=' ', end='\n', file=None)

    """
    kw.setdefault('file', sys.stdout)
    
    kw['file'].write(_p(*args, **kw))
