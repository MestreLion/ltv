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


def choose(options, candidate, tag, match=None):
    if not options:
        raise u.LegendasTVError("No %s found matching '%s'", tag, candidate)

    if match:
        options = tuple(filter(match, options))

    if len(options) == 1:
        return options[0]

    def tryint(text):
        try:               return int(text)
        except ValueError: return 0

    res = 0
    length = len(options)
    while not (1 <= res <= length):
        print(f"\nFound {length} {tag} matching '{candidate}':")
        for i, option in enumerate(options, 1):
            print(f"[{i:2d}] {option}")
        res = tryint(input("Your choice: "))
    return options[res - 1]




def interactive(path:str):
    if not ft.is_video(path):
        log.warning("File does not seem to be a Video: %s", path)

    guess = ft.guess_info(path)
    log.debug(repr(guess))

    video = model.VideoFile.from_guess(path, guess)
    log.debug(repr(video))

    ltv = tasks.get_ltv()

    # Good candidate for a model.VideoFile method
    def match_title(title):
        # Too many mis-categorized Titles in Legendas.TV (WestWorld Season 3 is Movie)
        #if not video.match_category(title):
        #    return False

        if video.category == model.Category.MOVIE  and video.year:
            return (title.year == video.year)

        if video.category == model.Category.SEASON and video.season:
            return (title.season == video.season)

        return True

    title = choose(ltv.search_titles(video.title), video, 'titles', match_title)
    video.titleobj = title
    log.debug("Chosen Title: %r", title)

    # Also a good candidate for a model.VideoFile method
    def match_subtitle(subtitle):
        if subtitle.subtype == model.SubType.PACK:
            return True
        episode = ft.guess_info(subtitle.release).get('episode')
        if (
                (video.titleobj and not video.titleobj.category == model.Category.MOVIE)
            and (video.episode and episode and not video.episode == episode)
        ):
            return False
        return True

    subtitle = choose(ltv.search_subtitles(title.id), video, 'subtitles', match_subtitle)
    video.subtitle = subtitle
    log.debug("Chosen Subtitle: %r", subtitle)

    archive = ltv.download_subtitle(subtitle.hash, system.save_cache_path(a.__title__))
    log.debug("Archive: %s", archive)

    def match_srt(srt):
        episode = ft.guess_info(srt).get('episode')
        if (video.episode and episode and not video.episode == episode):
            return False
        return True
    srt = choose(ft.extract_archive(archive, extlist='srt'), video, 'SRTs', match_srt)
    log.debug("Chosen SRT: %s", os.path.basename(srt))

    ft.rename_srt(srt, video.path)
    log.info("Done!")
