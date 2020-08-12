# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Command-line functions
"""

import argparse
import logging
import os
import sys
import typing as t

import argh

# Undo __init__'s NullHandler
logging.getLogger(__package__).handlers.clear()

from . import __about__ as a
from . import api
from . import filetools
from . import util as u


log = logging.getLogger(__name__)


# CLI command wrappers ###################################################

def search_titles(
        query:str,
        ) -> None:
    ltv = api.LegendasTV()
    for title in ltv.search_titles(query):
        yield(f"{title.id}\t{title.category}\t{title}")


def search_subtitles(
        title_id:int,
        ) -> None:
    ltv = api.LegendasTV()
    for sub in ltv.search_subtitles(title_id):
        print(f"{sub.hash}\t{sub}")

def extract(
        archive:   str,
        path:      str  = None,
        extlist:   list = None,
        keep:      bool = True,
        overwrite: bool = False,
        safe:      bool = True,
        recursion: int  = 1,
        ) -> None:
    """Extract files from an archive"""
    try:
        paths = filetools.extract_archive(
            archive,
            path,
            extlist,
            keep,
            overwrite,
            safe,
            recursion
        )
    except FileNotFoundError:
        raise u.LegendasTVError("Cannot extract archive, no such file: %s", archive)

    for path in paths:
        log.info(path)


# ########################################################################

def parse_args(argv:list=None) -> t.Tuple[argparse.Namespace, argh.ArghParser]:
    """Argument parsing and CLI interface setup"""
    parser = argh.ArghParser(
        prog            = __package__,
        description     = f"{a.__project__}\n{a.__description__}",
        epilog          = a.epilog,
        formatter_class = argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-q', '--quiet',
        dest='loglevel',
        const=logging.WARNING,
        default=logging.INFO,
        action="store_const",
        help="Suppress informative messages."
    )
    group.add_argument(
        '-v', '--verbose',
        dest='loglevel',
        const=logging.DEBUG,
        action="store_const",
        help="Verbose mode, output extra info."
    )

    argh.add_commands(parser, functions=(
        filetools.video_hash,
        filetools.guess_info,
        extract,
    ))
    argh.add_commands(parser, functions=(
        search_titles,
        search_subtitles,
    ))

    args = parser.parse_args(argv)
    args.debug = args.loglevel == logging.DEBUG
    logging.getLogger().setLevel(args.loglevel)  # could be done by cli()

    return args, parser


def cli(argv:list=None):
    """CLI main function"""
    logging.basicConfig(format='%(asctime).19s [%(levelname)-.5s] %(message)s')
    args, parser = parse_args(argv)
    log.debug(args)
    argh.dispatch(parser, argv)


def main(argv:list=None):
    """Main CLI entry point"""
    try:
        sys.exit(cli(argv or sys.argv[1:]))
    except u.LegendasTVError as e:
        log.critical(e)
        sys.exit(1)
    except BrokenPipeError:
        # https://docs.python.org/3/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    except Exception as e:
        log.critical(e, exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(2)  # signal.SIGINT.value
