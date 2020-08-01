# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

import logging
import os
import struct

import guessit

from . import util as u


log = logging.getLogger(__name__)


def video_hash(filename:str) -> str:
    """Return the OpenSubtitles video file hash.

    https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
    """
    block = 65536
    fmt = f"<{block//8}Q"  # 8 bytes * 8KiB (unsigned long long)
    vhash = os.path.getsize(filename) # initial value for hash is file size

    def partialhash(f):
        return sum(struct.unpack(fmt, f.read(block)))

    with open(filename, "rb") as f:
        try:
            vhash += partialhash(f)
            f.seek(-block, os.SEEK_END)
            vhash += partialhash(f)
            vhash &= 0xFFFFFFFFFFFFFFFF  # cap at 64bit
        except (IOError, struct.error):
            raise u.LegendasTVError("File must be at least %d bytes to hash: %s",
                                    block, filename)
    return f"{vhash:016x}"


def guess_info(filename:str) -> dict:
    return guessit.guessit(filename)
