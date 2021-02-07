# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Interactive CLI
"""

import logging
import os

from . import __about__ as a
from . import filetools as ft
from . import model
from . import system
from . import tasks
from . import util as u


log = logging.getLogger(__name__)


def choose(options, candidate, tag, fmatch=None, fdisplay=str):
    if not options:
        raise u.LegendasTVError("No %s found matching '%s'", tag, candidate)

    if fmatch:
        options = tuple(filter(fmatch, options))
        if not options:
            raise u.LegendasTVError("No %s found matching '%s' after filter.",
                                    tag, candidate)

    def tryint(text):
        try:               return int(text)
        except ValueError: return 0

    length = len(options)
    res = 1 if length == 1 else 0  # automatically bypass choice loop if single option
    while not (1 <= res <= length):
        print(f"\nFound {length} {tag}s matching '{candidate}':")
        for i, option in enumerate(options, 1):
            print(f"[{i:2d}] {fdisplay(option)}")
        res = tryint(input("Your choice: "))

    option = options[res - 1]
    log.info("Selected %s: %r", tag, fdisplay(option))
    log.debug(repr(option))
    return option


def interactive(path:str):
    if not ft.is_video(path):
        log.warning("File does not seem to be a Video: %s", path)

    guess = u.guess_info(path)
    log.debug(repr(guess))

    video = model.VideoFile.from_guess(path, guess)
    log.debug(repr(video))

    ltv = tasks.get_ltv()

    title    = choose(ltv.search_titles(video.title), video, 'Title',    video.match_title)
    subtitle = choose(ltv.search_subtitles(title.id), video, 'Subtitle', video.match_subtitle)

    archive = ltv.download_subtitle(subtitle.hash, system.save_cache_path(a.__title__))
    log.debug("Archive: %s", archive)

    srt = choose(ft.extract_archive(archive, extlist='srt'), video, 'SRT',
                 video.match_srt, os.path.basename)

    ft.copy_srt(srt, video.path)
    log.info("Done!")
