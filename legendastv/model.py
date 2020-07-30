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
    REGULAR  = ''
    PACK     = 'p'
    FEATURED = 'd'  # 'Destaque'


class Title:
    """Base Class for Movies, TV Series Seasons and Videos"""
    # TODO: Perhaps enforce this as Abstract Class to prevent direct instantiation
    #       Setting `category = None` is a good step but not enough
    category: t.ClassVar[t.Optional[Category]] = None

    # Populated on first cls.from_data() run, as it depends on __subclasses__
    _subclass_mapping: t.ClassVar[t.Dict[Category, 'Title']] = {}

    def __init__(self, **kwargs):
        self._ltv = kwargs.pop('_ltv', None)
        self._raw = kwargs.pop('_raw', None)
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
    def from_category(cls, category:Category, data:dict):
        """Return a Title subclass instance based on category"""
        # One-time subclass mapping population
        # Performed here to allow client extensions by sublassing
        if not cls._subclass_mapping:
            cls._subclass_mapping.update({s.category: s for s in cls._subclasses()})
        return cls._subclass_mapping[category](**data)

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
    _typechar_map = {
        SubType.PACK:     'P',
        SubType.FEATURED: '*',
    }

    def __init__(self, **kwargs):
        self._ltv = kwargs.pop('_ltv', None)
        self._raw = kwargs.pop('_raw', None)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def pack(self):
        return self.subtype == SubType.PACK

    @property
    def featured(self):
        return self.subtype == SubType.FEATURED

    def __repr__(self):
        fields = ['hash', 'release', 'username', 'date', 'downloads', 'subtype']
        return u.fullrepr(self, fields)

    def __str__(self):
        typechar = self._typechar_map.get(self.subtype, ' ')
        return f"<{self.url}> {typechar} {self.release}"
