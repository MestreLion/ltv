# Legendas.TV API - Search, download and extract subtitles from Legendas.TV website
#
#    Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>

"""
    Project metadata

The single source of truth for version number and related information.
Must be truly self-contained: do not import modules or read external files
Preferably only trivial string manipulations and basic list/tuple/dict operations
"""


# Main
# Literals only

__title__        = "legendastv"  # could be inferred from basename(dirname(__file__))
__project__      = "Legendas.TV API"
__description__  = "Search, download and extract subtitles from Legendas.TV website"
__url__          = "https://github.com/MestreLion/legendastv"

__author__       = "Rodrigo Silva (MestreLion)"
__email__        = "linux@rodrigosilva.com"

__version__      = "0.0.1"

__license__      = "GPLv3+"
__copyright__    = "Copyright (C) 2020 Rodrigo Silva"


# ../setup.py
# https://pypi.org/classifiers/
python_requires  = '>=3.6'  # Adjust __classifiers__ accordingly!
classifiers      = [
    "Development Status :: 2 - Pre-Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Multimedia :: Video",
    "Topic :: Utilities",
]
keywords         = "subtitles api library legendastv scraper"
entry_points     = {'console_scripts': [f'{__title__} = {__title__}.cli:main']}
install_requires = [
    'argh',
    'guessit',
    'requests',
    'unrar',
]
extras_require   = {
    'rarfile': ['rarfile'],
}
readme           = "README.md"
project_urls     = {"Bug Tracker": __url__ + "/issues", "Source Code": __url__}
package_data     = {'': ['*.md', 'LICENSE*']}


# ./cli.py

epilog = f"""{__copyright__}
License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""


# Possibly irrelevant
__status__ = "Prototype"


# Derived data
__version_info__ = tuple(map(int, __version__.split('-')[0].split('+')[0].split('.')[:3]))
if len(__version_info__) < 3: __version_info__ = (__version_info__ + 3*(0,))[:3]
