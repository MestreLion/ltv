#!/usr/bin/env python3
#
# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Download, build and "install" UnRAR Library

Inspired by unrardll/ci.py from Kovid Goyal
https://github.com/kovidgoyal/unrardll/blob/master/ci.py
"""

import glob
import io
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request


HOST  = 'http://www.rarlab.com/'
INDEX = 'rar_add.htm'
SRCRE = re.compile(r'rar/unrarsrc-(.+?)\.tar\.gz')  # Per debian/watch from unrar-nonfree

HERE  = os.path.abspath(os.path.dirname(__file__))

log = logging.getLogger(__name__)


def download(url:str) -> bytes:
    log.debug('HTTP GET %r', url)
    with urllib.request.urlopen(url) as res:
        return res.read()


def get_source_info() -> tuple:
    match = re.search(SRCRE, download(HOST + INDEX).decode('utf-8', 'ignore'))
    return match.group(1), HOST + match.group(0)


def extract(data:bytes, path:str) -> None:
    log.debug("Extracting to %r", path)
    def is_safe(name):
        return not(name.startswith('/') or name.startswith('../') or '/../' in name)
    with io.BytesIO(data) as fd:
        with tarfile.open(fileobj=fd) as tar:
            tar.extractall(path, members=(member for member in tar
                                          if is_safe(member.name)))


def replace_inplace(filepath:str, old:str, new:str) -> None:
    with open(filepath) as f:
        text = f.read()
    if old not in text:
        return
    with open(filepath, "w") as f:
        f.write(text.replace(old, new))


def execute(*args:str) -> bool:
    log.debug("Executing: %s", ' '.join(args))
    try:
        subprocess.check_call(args)
        return True
    except subprocess.CalledProcessError as e:
        log.error(e)
        return False


def build_unix(osx=False) -> None:
    lib = 'libunrar.so'
    if osx:
        osxlib = lib.replace('.so', 'dylib')
        replace_inplace('makefile', lib, osxlib)
        lib = osxlib
    if execute('make', '-s', 'lib'):
        shutil.copy2(lib, HERE)


def build_windows() -> None:
    # See NOTE at https://docs.python.org/3/library/platform.html#platform.architecture
    arch = 'x64' if sys.maxsize > 2**32 else 'Win32'
    replace_inplace('dll.cpp', 'WideToChar', 'WideToUtf')
    if execute(
        'msbuild.exe',
        'UnRARDll.vcxproj',
        '/t:Build',
        '/p:Platform=' + arch,
        '/p:Configuration=Release'
    ):
        for lib in ('UnRAR.lib', 'unrar.dll'):
            shutil.copy2(glob.glob('./build/*/Release/' + lib)[0], HERE)


def main(argv:list=None):  # @UnusedVariable
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime).19s %(levelname)-5s] %(message)s')

    if argv:
        if '--clean' in argv:
            for __ in ('unrar-*/', 'UnRAR.lib', 'unrar.dll', 'libunrar.*'):
                for path in glob.glob(os.path.join(HERE, __)):
                    if path[-1:] == '/':
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
        #elif ...
        else:
            print(__doc__.strip().split('\n')[0])
            print('Usage: ./install.py [-h|--help] [--clean]')
        return

    log.info("Checking UnRAR latest version")
    version, url = get_source_info()
    path = os.path.join(HERE, "unrar-" + version)

    log.info("Downloading and extracting source archive")
    extract(download(url), path)

    log.info("Building UnRAR")
    os.chdir(os.path.join(path, 'unrar'))
    platform = sys.platform.lower()
    if   platform.startswith('linux'):  build_unix()
    elif platform.startswith('darwin'): build_unix(osx=True)
    elif platform.startswith('win'):    build_windows()
    else:
        log.error("Unknown platform: %s", platform)
        return 3

    log.info("Done!")


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        log.critical(e)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(2)  # signal.SIGINT.value
