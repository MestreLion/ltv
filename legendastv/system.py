# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2021 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Platform-dependent methods in an implementation-independent way

Inspired by pyxdg, appdirs and xdgappdirs.
"""

import logging
import os
import sys


# "Enums"
WINDOWS = 'win'
LINUX   = 'linux'
MACOS   = 'darwin'
UNKNOWN = ''  # Falsy value to allow `if not platform:`, as used below

# Let's pretend this module is 100% reusable
_APPTITLE = os.path.basename(os.path.dirname(__file__))


log = logging.getLogger(__name__)

_platform = sys.platform.lower()
platform = (LINUX   if _platform.startswith(LINUX)   else
           (MACOS   if _platform.startswith(MACOS)   else
           (WINDOWS if _platform.startswith(WINDOWS) else
            UNKNOWN)))

if not platform:  # platform == UNKNOWN
    log.warning("Unknown platform: %s", sys.platform)

home = os.path.expanduser('~')


# Data
if   platform == LINUX:
    data_home = os.environ.get('XDG_DATA_HOME') or os.path.join(home, '.local', 'share')
elif platform == MACOS:
    data_home = os.path.join(home, 'Library', 'Application Support')
elif platform == WINDOWS:
    data_home = os.environ.get('LOCALAPPDATA') or home
else:
    data_home = home


# Config
if   platform == LINUX:
    config_home = os.environ.get('XDG_CONFIG_HOME') or os.path.join(home, '.config')
elif platform == MACOS:
    # Do NOT use ~/Library/Preferences/ on MACOS! That's for .plists!
    # Use of XDG_DATA_HOME on Mac is debatable, and I'm intentionally deviating from spec,
    # using '~/Library/Application Support' instead of ~/.config as default *when not set*
    config_home = os.environ.get('XDG_CONFIG_HOME') or data_home
else:
    config_home = data_home


# Cache
if   platform == LINUX:
    cache_home = os.environ.get('XDG_CACHE_HOME') or os.path.join(home, '.cache')
elif platform == MACOS:
    cache_home = os.path.join(home, 'Library', 'Caches')
else:
    cache_home = data_home


# Logs
if   platform == MACOS:
    log_home = os.path.join(home, 'Library', 'Logs')
else:
    log_home = cache_home


def _save_path(path, apptitle="", vendor=None, mode=0o777, suffix=""):
    if not apptitle:
        apptitle = _APPTITLE
    assert not apptitle.startswith('/')
    if vendor is False or not platform == WINDOWS:
        path = os.path.join(path, apptitle)
    elif vendor is None:
        path = os.path.join(path, apptitle, apptitle)
    else:
        path = os.path.join(path, vendor, apptitle)
    if suffix:
        path = os.path.join(path, suffix)
    os.makedirs(path, mode, exist_ok=True)
    return path


def save_data_path(apptitle="", vendor=None):
    """Return the data path for the application, creating it if necessary.

    Data path is usually in the form ``<data_home>/[<vendor>/]<apptitle>``,
    <vendor> is used only on Windows and if not False, ignored otherwise,
    and defaults to <apptitle>.

    Use this when saving or updating application data.
    """
    return _save_path(data_home, apptitle, vendor)


def save_config_path(apptitle="", vendor=None):
    """Return the config path for the application, creating it if necessary.

    Use this when saving or updating application settings and configuration.
    """
    return _save_path(config_home, apptitle, vendor, mode=0o700)


def save_cache_path(apptitle="", vendor=None):
    """Return the cache path for the application, creating it if necessary.

    Use this for temporary files.
    """
    suffix = 'Cache' if platform == WINDOWS else ""
    return _save_path(cache_home, apptitle, vendor, suffix=suffix)


def save_log_path(apptitle="", vendor=None):
    """Return the log path for the application, creating it if necessary.

    Use this for log files.
    """
    if   platform == LINUX:   suffix = 'log'
    elif platform == WINDOWS: suffix = 'Logs'
    else:                     suffix = ''
    return _save_path(log_home, apptitle, vendor, mode=0o700, suffix=suffix)
