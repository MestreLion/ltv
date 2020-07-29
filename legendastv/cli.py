# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Command-line functions
"""

import argparse
import logging

from . import __about__ as a


log = logging.getLogger(__name__)


def parse_args(argv:list=None) -> argparse.Namespace:
    """Argument parsing and CLI interface setup"""
    parser = argparse.ArgumentParser(
        prog            = __package__,
        description     = f"{a.__project__}\n{a.__description__}",
        epilog          = a.epilog,
        formatter_class = argparse.RawDescriptionHelpFormatter
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet',
                       dest='loglevel',
                       const=logging.WARNING,
                       default=logging.INFO,
                       action="store_const",
                       help="Suppress informative messages.")

    group.add_argument('-v', '--verbose',
                       dest='loglevel',
                       const=logging.DEBUG,
                       action="store_const",
                       help="Verbose mode, output extra info.")

    parser.add_argument('-a', '--arg',
                        default="somearg",
                        help="Some Arg."
                            " [Default: %(default)s]")

    parser.add_argument('-o', '--option',
                        dest='option',
                        default=False,
                        action="store_true",
                        help="Some Option.")

    parser.add_argument(nargs='*',
                        dest='files',
                        help="Some files.")

    args = parser.parse_args(argv)
    args.debug = args.loglevel == logging.DEBUG
    log.setLevel(args.loglevel)

    return args


def main(argv:list=None):
    """Main CLI entry point"""
    args = parse_args(argv)
    logging.basicConfig(level=args.loglevel,
                        format='%(asctime).19s [%(levelname)-.5s] %(message)s')
    log.debug(args)
    print("Legendas.TV!")
