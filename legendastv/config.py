# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Handle Configuration, Settings and Authorization files, mostly for CLI
"""

import logging
import os

try:
    import keyring
except ImportError:
    keyring = None

from . import __about__ as a
from . import system
from . import util as u


# Factory settings, lowercase options can be changed at config file
OPTIONS = {
#   'CACHEDIR'      : system.save_cache_path(a.__title__),
    'debug'         : True,
    'cache'         : True,
    'notifications' : True,
    'language'      : "pb",
}
AUTH = {
    'username'      : "",
    'password'      : "",
}

log = logging.getLogger(__name__)


def read_config(args, apptitle="") -> dict:  # @UnusedVariable
    """Read the configuration file, update the OPTIONS dictionary and return it"""
    confpath = args.config or save_config_path(apptitle)  # @UnusedVariable, for now...
    # Create a blank one if none exists...
    # ...
    # Read the file
    # ...
    OPTIONS.update({})
    return OPTIONS


def save_config_path(apptitle="") -> str:
    """Return the path to the config file, ensuring its tree exists"""
    apptitle = apptitle or a.__title__
    return os.path.join(system.save_config_path(apptitle), f"{apptitle}.ini")


def read_auth(args, apptitle="") -> dict:
    """Read/write the credentials, update the AUTH dictionary and return it"""

    def keyring_get(apptitle):
        # Workaround keyring first run issue: https://github.com/jaraco/keyring/issues/391
        authfile = args.authfile or save_auth_path(apptitle)
        if not os.path.isfile(authfile):
            log.debug("Creating a dummy auth file to workaround keyring issue #391")
            keyring_set(apptitle, "", "")  # Set dummy data, so it picks the main backend
            open(authfile, 'a').close()    # disable workaround trigger
        try:
            return (keyring.get_password(apptitle, apptitle).split('\n') + ['\n'])[:2]
        except keyring.errors.KeyringLocked as e:
            raise u.LegendasTVError(e)
        except keyring.errors.InitError as e:
            log.error("Keyring workwaround failed: %s", e)
            return "", ""
        except IOError as e:  # gnome-keyring used to raise this. FIXME: Does it still?
            log.error(e)
            return "", ""

    def keyring_set(apptitle, username, password):
        keyring.set_password(apptitle, apptitle, '{}\n{}'.format(username, password))

    apptitle = apptitle or a.__title__

    # read
    username = ""
    password = ""
    if keyring:
        log.debug("Reading credentials from keyring")
        username, password = keyring_get(apptitle)
    else:
        try:
            authfile = args.authfile or save_auth_path(apptitle)
            log.debug("Reading credentials from: %s", authfile)
            with open(authfile, 'r') as fd:
                username, password = (fd.read().splitlines() + ['\n'])[:2]
        except FileNotFoundError:
            pass  # will be dealt with later
        except IOError as e:
            log.error(e)

    # save
    if args.username or args.password:
        log.info("Saving credentials")
        username = args.username or username
        password = args.password or password
        if keyring:
            keyring_set(apptitle, username, password)
        else:
            authfile = args.authfile or save_auth_path(apptitle)
            try:
                with open(authfile, 'w') as fd:
                    fd.write("{}\n{}\n".format(username, password))
                os.chmod(authfile, 0o600)
            except IOError as e:
                log.error(e)

    if username and password:
        AUTH.update({'username': username,
                     'password': password})
    else:
        log.warning("Credentials not set, first time usage?"
                    " Some features will not be available,"
                    " such as downloading subtitles.")

    return AUTH


def save_auth_path(apptitle=""):
    """Return the path to the auth credentials file, ensuring its tree exists"""
    return os.path.join(system.save_config_path(apptitle or a.__title__), "login.auth")
