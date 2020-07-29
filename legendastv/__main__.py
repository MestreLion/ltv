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
    Convenience package launcher. Allow `python -m legendastv` invocation
"""

import logging
import os
import sys

from . import cli

log = logging.getLogger(__package__)

try:
    sys.exit(cli.main(sys.argv[1:]))
except BrokenPipeError:
    # https://docs.python.org/3/library/signal.html#note-on-sigpipe
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
except Exception as e:
    log.critical(e, exc_info=True)
    sys.exit(1)
except KeyboardInterrupt:
    sys.exit(2)  # signal.SIGINT.value
