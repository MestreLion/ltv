# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Data Classes
"""

import enum
import logging
import typing as t

from . import util as u


log = logging.getLogger(__name__)

TTitle = t.TypeVar('TTitle', bound='Title')


class Category(enum.Enum):
    MOVIE   = 'M'
    SEASON  = 'S'
    CARTOON = 'C'


class SubType(enum.Enum):
    PACK     = 'p'
    FEATURED = 'd'  # 'Destaque'


class Title:
    """Base Class for Movies, TV Series Seasons and Videos"""
    # TODO: Perhaps enforce this as Abstract Class to prevent direct instantiation
    #       Setting `category = None` is a good step but not enough
    category: t.ClassVar[t.Optional[Category]] = None

    _data_mapping = dict(
        id       = 'id_filme',
        category = 'tipo',  # used to determine subclass
        title    = 'dsc_nome',
        native   = 'dsc_nome_br',
        thumb    = 'dsc_imagen',
        year     = 'dsc_data_lancamento',
        season   = 'temporada',  # only for Season subclass
        imdb_id  = 'id_imdb',
        synopsis = 'dsc_sinopse',
        user_id  = 'id_usuario',

        # Unused fields and example values:
        # "int_genero":         "1021",
        # "dsc_sinopse":        "...",
        # "dsc_url_imdb":       "http://www.imdb.com/title/tt0082186/",
        # Not derived from 'id_imdb', not standartized. Real examples:
        # [36413] "http://www.imdb.com/title/tt2338096/" - Most common
        # [41202] "http://www.imdb.com/title/tt2314952"  - No trailing slash
        # [81698] "http://uk.imdb.com/title/tt0081698"   - Alt subdomain
        # [22597] "www.imdb.com/title/tt1216475/"        - Missing scheme
        # "soundex":            "KLXF0TTNS",
        # "flg_liberado":       "1",
        # "dsc_data_liberacao": None,
        # "dsc_data":           None,
        # "dsc_metaphone_us":   "KLXF0TTNS",
        # "dsc_metaphone_br":   "FRTTTS",
        # "episodios":          None,
        # "flg_seriado":        None,
        # "last_used":          "1373185369",
        # "deleted":            False,
    )
    # Populated on first cls.from_data() run, as it depends on __subclasses__
    _subclass_mapping: t.ClassVar[t.Dict[Category, 'Title']] = {}

    def __init__(self, **kwargs):
        self._raw = kwargs.pop('raw', None)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def imdb_url(self) -> str:
        if not getattr(self, 'imdb_id', None): return ""
        return f"https://www.imdb.com/title/tt{self.imdb_id:07}/"

    @classmethod
    def _subclasses(cls) -> t.Set[TTitle]:
        """Set of all subclasses, recursively"""
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(subclass._subclasses())
        return subclasses

    @classmethod
    def from_data(cls, data:dict) -> TTitle:
        """Parse JSON raw data to a Title subclass instance."""
        # TODO: Possibily move to api.search_title() to allow thin, generic
        #       data classes such as Subtitle.

        # One-time subclass mapping population
        # Performed here to allow client extensions by sublassing
        if not cls._subclass_mapping:
            cls._subclass_mapping.update({s.category: s for s in cls._subclasses()})

        # Map raw JSON data to class attributes
        try:
            kwargs = {k: data['_source'].get(v) for k, v in cls._data_mapping.items()}
        except KeyError as e:
            raise u.LegendasTVError("Missing expected key %r: %s", e.message, data)

        # Type casting and data formatting
        for k in ('id', 'year', 'season', 'imdb_id', 'user_id'): kwargs[k] = u.toint(kwargs[k])
        try:
            category = Category(kwargs.pop('category'))
        except ValueError as e:
            # 'X' is not a valid Category
            raise u.LegendasTVError("%s: %s", e.args[0], data)

        # Integrity checks
        if category == Category.MOVIE and kwargs['season']:
            log.warning("Movie with season (%r): %s", kwargs['season'], data)
        if category == Category.SEASON and not kwargs['season']:
            log.warning("Season with invalid season (%r): %s", kwargs['season'], data)
        if not (kwargs['title'] and kwargs['native']):
            log.warning("Empty original or native title: %s", data)

        # Inject source data, for future use
        kwargs['raw'] = data

        return cls._subclass_mapping[category](**kwargs)

    def __repr__(self):
        return u.fullrepr(self, ('id', 'year', 'title', 'imdb_id'))

    def __str__(self):
        s = self.title.strip()
        if self.season:                               s += f" S{self.season:02}"
        if self.native and self.native != self.title: s += f" [{self.native.strip()}]"
        if self.year:                                 s += f" - {self.year}"
        return s.strip()


class Movie(Title):
    """Movie, including Feature Films, TV Movies and others"""
    category: t.ClassVar[Category] = Category.MOVIE


class Season(Title):
    """TV Series Season"""
    category: t.ClassVar[Category] = Category.SEASON

    def __repr__(self):
        return u.fullrepr(self, ('id', 'season', 'year', 'title', 'imdb_id'))


class Cartoon(Season):
    """Mostly TV Cartoon Series, some listed as Video in IMDB

    A hybrid between Movie and Season, season number is optional
    """
    category: t.ClassVar[Category] = Category.CARTOON


class Subtitle:
    """Subtitle archive"""
    def __init__(self, **kwargs):
        self._raw = kwargs.pop('raw', None)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def flags(self):
        s = ''
        if   self.pack:     s += 'P'
        elif self.featured: s += '*'
        return s

    def __repr__(self):
        fields = ['hash', 'release', 'username', 'date', 'downloads']
        if   self.pack:     fields.append('pack')
        elif self.featured: fields.append('featured')
        return u.fullrepr(self, fields)

    def __str__(self):
        return f"<{self.url}> {self.flags:1} {self.release}"
