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

from . import __about__ as a
from . import util as u


log = logging.getLogger(__name__)


def parse_args(argv:list=None) -> argparse.Namespace:
    """Argument parsing and CLI interface setup"""
    parser = argparse.ArgumentParser(
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

    args = parser.parse_args(argv)
    args.debug = args.loglevel == logging.DEBUG
    log.setLevel(args.loglevel)

    return args


def cli(argv:list=None):
    """CLI main function"""
    logging.basicConfig(format='%(asctime).19s [%(levelname)-.5s] %(message)s')
    args = parse_args(argv)
    log.debug(args)
    print("Legendas.TV!")


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
