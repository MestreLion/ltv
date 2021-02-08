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


def choose(options, candidate, tag, fmatch=None, fdisplay=str, filters:dict=None):
    if not options:
        raise u.LegendasTVError("No %s found matching '%s'", tag, candidate)

    if filters:
        options = u.match_filter(options, **filters)

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


def interactive(
        path:str,
        title:str=None, year:int=None, season:int=None, category:model.Category=None,
        direct:bool=False,
    ):
    """Interactive mode to search, download, extract and rename subtitles.

    Will ask to choose a Title, Subtitle and SRT if needed.

    <direct> skip Title search, which usually lead to many (unrelated) Subtitle choices.

    Usually the Video (full) path is enough for relevant choices, use <filters> to
      force an exact match on any Title or Subtitle attribute, narrowing down choices.
      (for `category`, use either `movie`, `season` (for series' episodes) or `cartoon`)
    """
    if isinstance(category, str):
        category = model.Category.from_string(category)

    if not ft.is_video(path):
        log.warning("File does not seem to be a Video: %s", path)

    guess = u.guess_info(path)
    log.debug(repr(guess))

    video = model.VideoFile.from_guess(path, guess)
    log.debug(repr(video))

    ltv = tasks.get_ltv()

    if direct:
        search = dict(query=video.title)
    else:
        tid = choose(
            ltv.search_titles(video.title), video, 'Title', video.match_title,
            filters=dict(title=title, year=year, season=season, category=category)
        ).id
        search = dict(title_id=tid)

    subtitle = choose(
        ltv.search_subtitles(**search), video, 'Subtitle', video.match_subtitle,
        filters=(dict(title=title.replace(' ', '_')) if title is not None else {})
    )

    archive = ltv.download_subtitle(subtitle.hash, system.save_cache_path(a.__title__))
    log.debug("Archive: %s", archive)

    srt = choose(ft.extract_archive(archive, extlist='srt'), video, 'SRT',
                 video.match_srt, fdisplay=os.path.basename)

    ft.copy_srt(srt, video.path)
    log.info("Done!")
