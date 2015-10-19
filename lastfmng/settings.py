# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
import os

from .helpers.searchlists import RegexpSearchlist, StringSearchlist
from .compat import ConfigParser, NoOptionError
from .logging import setup_logging


setup_logging()
log = logging.getLogger(__name__)


config_files = [
    'defaults.ini',
    'config.ini',
    'lastfm.ini',
]


def load_config(config_files):
    config = None
    for config_file in config_files:
        config = load_config_file(config_file, config)
    return  config


def load_config_file(name, config=None):
    if not config:
        config = ConfigParser()
    try:
        with open(os.path.join(os.path.dirname(__file__), name)) as fp:
            config.readfp(fp)
    except IOError:
        pass
    return config


def get_config(section, name, type=''):
    try:
        return getattr(config, 'get{}'.format(type))(section, name)
    except NoOptionError:
        pass


config = load_config(config_files)


LASTFM_HOST = config.get('global', 'lastfm_host')
LASTFM_PORT = config.getint('global', 'lastfm_port')
LASTFM_KEY = config.get('global', 'lastfm_key')
log.info('host: %s:%s', LASTFM_HOST, LASTFM_PORT)
log.info('key: %s', LASTFM_KEY)


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


class Category(object):
    def __init__(self, name, searchlist=None):
        self.name = name
        self.searchlist = self.load_searchlist(searchlist)

    def __unicode__(self):
        return self.name

    @property
    def is_enabled(self):
        value = self.tag_config('enabled', 'boolean')
        return value if value is not None else True

    @property
    def threshold(self):
        value = self.tag_config('threshold', 'float')
        return value if value is not None else 0.5

    @property
    def limit(self):
        value = self.tag_config('limit', 'int')
        return value if value is not None else 4

    @property
    def overflow(self):
        value = self.tag_config('overflow')
        return value if value is not None else None

    @property
    def sort(self):
        value = self.tag_config('sort', 'boolean')
        return value if value is not None else False

    @property
    def titlecase(self):
        value = self.tag_config('titlecase', 'boolean')
        return value if value is not None else True

    @property
    def separator(self):
        value = self.tag_config('separator')
        return value.strip('"') if value else None

    def tag_config(self, key, type=''):
        value = get_config('category-{}'.format(self.name), key, type)
        if value is None:
            value = get_config('category-{}'.format('defaults'), key, type)
        return value

    def load_searchlist(self, searchlist=None):
        # default to a string searchlist and load config by name
        if not searchlist:
            searchlist = StringSearchlist(config.get('searchlist', self.name))
        # exclude 'soundtrack' as a tagname
        if get_config('global', 'soundtrack_is_no_genre', 'boolean'):
            searchlist.remove('soundtrack')
        return searchlist

    def filter_tags(self, all_tags):
        l = 5

        # exclude tags not relevant for this category
        tags = [
            (tag, score) for tag, score in all_tags
            if tag in self.searchlist
        ]

        # exclude tags below the threshold
        #
        # The threshold is meant to remove tags that are extremely rare
        # compared to the most popular one. When there are only very few tags
        # in a category even a very seldom used tag would be considered
        # otherwise.
        #
        # For example:
        #   assume we allow 2 tags in the 'decade' category
        #   found tags are: '90s' with score 900 and '70s' with score 200
        #   ... so somebody probably tagged this '70s' by mistake
        #   ... with a configured threshold of 0.5 any tag with score less
        #       than 450 would not be considered in this example.
        #
        if tags:
            log.info('%s: %s tag(s) before threshold filter:',
                self, len(tags))
            log.info('%s: %s%s', self,
                ', '.join(['{} ({})'.format(t, s) for t, s in tags][:l]),
                ', ...' if len(tags) > l else '',
            )

            #TODO make sure they are sorted by score
            threshold = self.get_threshold(tags[0])
            tags = [
                (tag, score) for tag, score in tags
                if score >= threshold
            ]

            log.info('%s: %s tag(s) filtered:', self, len(tags))
            log.info('%s: %s%s', self,
                ', '.join(['{} ({})'.format(t, s) for t, s in tags][:l]),
                ', ...' if len(tags) > l else '',
            )
        else:
            log.info('%s: no tags', self)

        return tags

    def get_threshold(self, tag):
        threshold = int(float(tag[1]) * self.threshold)
        log.info('%s: score threshold = %s (%.0f%%)',
            self, threshold, self.threshold * 100)
        return threshold


CATEGORIES = [
    # grouping is used as major/high level category
    Category('grouping'),
    Category('genre'),
    # eg. angry, cheerful, clam, ...
    Category('mood'),
    # eg. background, late night, party
    Category('occasion'),
    # i don't really know
    Category('category'),
    # country names
    Category('country'),
    # city names
    Category('city'),
    # musical era, eg. 80s, 90s, ...
    Category('decade', RegexpSearchlist("^([1-9][0-9])*[0-9]0s$")),
    # the full year, eg. 1995, 2000, ...
    Category('year', RegexpSearchlist("^[1-9][0-9]{3}$")),
]
log.info('categories: %s', ', '.join([
        '{} ({})'.format(c.name, c.limit)
        for c
        in CATEGORIES
        if c.is_enabled == True
    ]))


def translate_tag(name):
    try:
        name = config.get('translations', name.lower())
    except:
        pass
    return name
