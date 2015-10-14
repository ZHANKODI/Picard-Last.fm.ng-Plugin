# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from .helpers.experimental import SearchTree
from .helpers.searchlists import RegexpSearchlist, StringSearchlist

from .compat import ConfigParser, OrderedDict


config_file = os.path.join(os.path.dirname(__file__), "config.ini")
config = ConfigParser()
config.readfp(open(config_file))


LASTFM_HOST = config.get('global', 'lastfm_host')
LASTFM_PORT = config.getint('global', 'lastfm_port')
LASTFM_KEY = config.get('global', 'lastfm_key')


ENABLE_COLLECT_UNUSED = config.getboolean('global', 'collect_unused')


DEBUG_STATS = config.getboolean('global', 'print_tag_stats')
DEBUG_STATS_TRACK = config.getboolean('global', 'print_tag_stats_track') \
    if DEBUG_STATS else False
DEBUG_STATS_ALBUM = config.getboolean('global', 'print_tag_stats_album') \
    if DEBUG_STATS else False

DEFAULT_UNKNOWN = config.get('global', 'default_unknown').strip()


# toptag to metatag configuration
CONFIG = {
    # on album level set the following metadata
    'album': {
        # multiplication factors for each type of toptag
        'weight': dict(album=15, all_artist=55, all_track=30),
        'tags': {
            # category  metatag
            'grouping': 'albumgrouping',
            'genre': 'albumgenre',
            'mood': 'albummood',
        }
    },
    # for each track set the following metadata
    'track': {
        # TODO *plus supports disabling toptag types per metatag... eg. country only via artist toptags.
        'weight': dict(artist=2, track=8),
        'tags': {
            # category  metatag
            'grouping': 'grouping',
            'genre': 'genre',
            'mood': 'mood',
            'year': 'year',
            'occasion': 'comment:Songs-DB_Occasion',
            'decade': 'comment:Songs-DB_Custom1',
            'category': 'comment:Songs-DB_Custom2',
            'city': 'comment:Songs-DB_Custom3',
            'country': 'comment:Songs-DB_Custom4',
        }
    }
}




# TODO integrate CONFIG stuff into this dict
CATEGORIES = OrderedDict([
    # grouping is used as major/high level category
    ('grouping', dict(
        # limit: a hard limit for how many toptags are assigned to the metatag
        # threshold: percentage; only the toptags with a score above are used
        # enabled: don't collect toptags for that category
        # sort: alphabetically sort toptags before joining to string
        # titlecase: apply titlecase() function to each toptag
        # separator: used to join toptags if >1 are to be used
        #   (None to use multtag)
        # unknown: the string to use if no toptag was found for the category
        # overflow: name of another category, unused toptags in this category
        #     will be used in the given one.
        searchlist=StringSearchlist(config.get('searchlist', 'grouping')),
        limit=1, threshold=0.5, enabled=True, sort=False, titlecase=True,
        separator=", ", unknown=DEFAULT_UNKNOWN, overflow='genre')),

    ('genre', dict(
        searchlist=StringSearchlist(config.get('searchlist', 'genre')),
        limit=4, threshold=0.5, enabled=True, sort=False, titlecase=True,
        separator=None, unknown=DEFAULT_UNKNOWN)),

    # eg. angry, cheerful, clam, ...
    ('mood', dict(
        searchlist=StringSearchlist(config.get('searchlist', 'mood')),
        limit=4, threshold=0.5, enabled=True, sort=False, titlecase=True,
        separator=None, unknown=DEFAULT_UNKNOWN)),

    # eg. background, late night, party
    ('occasion', dict(
        searchlist=StringSearchlist(config.get('searchlist', 'occasion')),
        limit=4, threshold=0.5, enabled=True, sort=False, titlecase=True,
        separator=None, unknown=DEFAULT_UNKNOWN)),

    # i don't really know
    ('category', dict(
        searchlist=StringSearchlist(config.get('searchlist', 'category')),
        limit=4, threshold=0.5, enabled=True, sort=False, titlecase=True,
        separator=None, unknown=DEFAULT_UNKNOWN)),

    # country names
    ('country', dict(
        searchlist=StringSearchlist(config.get('searchlist', 'country')),
        limit=2, threshold=0.7, enabled=True, sort=True, titlecase=True,
        separator=None, unknown=DEFAULT_UNKNOWN)),

    # city names
    ('city', dict(
        searchlist=StringSearchlist(config.get('searchlist', 'city')),
        limit=1, threshold=0.7, enabled=True, sort=True, titlecase=True,
        separator=None, unknown=DEFAULT_UNKNOWN)),

    # musical era, eg. 80s, 90s, ...
    ('decade', dict(
        searchlist=RegexpSearchlist("^([1-9][0-9])*[0-9]0s$"),
        limit=1, threshold=0.7, enabled=True, sort=True, titlecase=False,
        separator=", ", unknown=DEFAULT_UNKNOWN)),

    # the full year, eg. 1995, 2000, ...
    ('year', dict(
        searchlist=RegexpSearchlist("^[1-9][0-9]{3}$"),
        limit=1, threshold=0.7, enabled=False, sort=True, titlecase=False,
        separator=", ", unknown=DEFAULT_UNKNOWN)),
])


if config.getboolean('global', 'soundtrack_is_no_genre'):
    CATEGORIES['grouping']['searchlist'].remove('soundtrack')
    CATEGORIES['genre']['searchlist'].remove('soundtrack')


# From http://www.last.fm/api/tos, 2011-07-30
# 4.4 (...) You will not make more than 5 requests per originating IP address
# per second, averaged over a 5 minute period, without prior written consent.
from picard.webservice import REQUEST_DELAY

REQUEST_DELAY[(LASTFM_HOST, LASTFM_PORT)] = 200


def translate_tag(name):
    try:
        name = config.get('translations', name.lower())
    except:
        pass
    return name