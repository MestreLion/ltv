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
from . import config
from . import system
from . import util as u


log = logging.getLogger(__name__)


# CLI command wrappers ###################################################

def search_titles(
        query:str,
        ) -> None:
    """List Titles matching a search query"""
    for title in api.LegendasTV().search_titles(query):
        yield(f"{title.id}\t{title.category}\t{title}")


def search_subtitles(
        title_id:int,
        ) -> None:
    """List Subtitles from a Title (by ID)"""
    for sub in api.LegendasTV().search_subtitles(title_id):
        print(f"{sub.hash}\t{sub}")


def download_subtitle(
        filehash:  str,
        savedir:   str  = "",
        basename:  str  = "",
        overwrite: bool = True,
        ) -> None:
    """Download a Subtitle (by Hash) and print its path.

    By default downloads to the cache directory, use '.' for current dir.
    """
    if not (config.AUTH['username'] and config.AUTH['password']):
        raise u.LegendasTVError("Subtitle download requires authentication,"
                                " please try again using --username and --password"
                                " to set your credentials.")
    ltv = api.LegendasTV(config.AUTH['username'], config.AUTH['password'])
    savedir = savedir or system.save_cache_path(a.__title__)
    print(ltv.download_subtitle(filehash, savedir, basename, overwrite))


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
    parser.add_argument('-C', '--config', help="Path for an alternate configuration file")

    group = parser.add_argument_group("Authentication Options")
    group.add_argument('-U', '--username', dest='username',
                        help="Legendas.TV username, will be saved for future uses.")
    group.add_argument('-P', '--password', dest='password',
                        help="Legendas.TV password, will be saved for future uses.")
    group.add_argument('-A', '--authfile', dest='authfile',
                        help="Path for an alternate auth credentials file."
                             " Ignored if storing credentials in keyring.")

    argh.add_commands(parser, functions=(
        filetools.video_hash,
        filetools.guess_info,
        extract,
    ))
    argh.add_commands(parser, functions=(
        search_titles,
        search_subtitles,
        download_subtitle,
    ))

    args = parser.parse_args(argv)
    args.debug = args.loglevel == logging.DEBUG
    logging.getLogger().setLevel(args.loglevel)  # could be done by cli()

    return args, parser


def cli(argv:list=None):
    """CLI main function"""
    logging.basicConfig(format='%(levelname)-8s: %(message)s')
    # rebulk, used by guessit, is too chatty at DEBUG level
    logging.getLogger('rebulk').setLevel(logging.WARNING)

    args, parser = parse_args(argv)
    log.debug(args)

    config.read_config(args)
    config.read_auth(args)

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
