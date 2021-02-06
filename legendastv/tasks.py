# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Task-oriented functions, the building blocks for CLI, Interactive and Auto modes

These are all prime candidates to be converted to methods of the model classes
"""

from . import api
from . import config
from . import util as u


def get_ltv(auth=True):
    if not auth:
        return api.LegendasTV()
    if not (config.AUTH['username'] and config.AUTH['password']):
        raise u.LegendasTVError("Subtitle download requires authentication,"
                                " please try again using --username and --password"
                                " to set your credentials.")
    return api.LegendasTV(config.AUTH['username'], config.AUTH['password'])
