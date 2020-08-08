# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

import logging
import os
import pprint
import struct
import zipfile

import guessit

from . import util as u


# Declared before imports are done so alternatives can be logged
log = logging.getLogger(__name__)


# RAR archive support
try:
    import rarfile
    log.debug("Handling RAR archives with rarfile")
except ImportError:
    try:
        from unrar import rarfile
        log.debug("Handling RAR archives with unrar")
    except ImportError:
        log.warning("No module to extract RAR archives was found")
        rarfile = None


# Mimetype guessing
try:
    from gi.repository import Gio
    log.debug("Using mimetypes from Gio")

    def mimetype(filepath:str) -> str:
        """Return the guessed mimetype of a file based on extension or initial content.

        For paths with an extension, determine mimetype based solely on its
        extension. For extensionless files, try to perform a 1MB read and return
        'inode/directory' for directories and 'application/octet-stream' for unknown
        types and unreadable files (not found, broken symlinks or access denied).
        """
        mime = Gio.content_type_guess(filename=filepath, data=None)[0]
        if extension(filepath):
            return mime

        try:
            with open(filepath, 'rb') as f:
                return Gio.content_type_guess(filename=None, data=f.read(1024**2))[0]
        except IsADirectoryError:
            return 'inode/directory'  # same output as when filepath ends with '/'
        except (FileNotFoundError, PermissionError):
            return 'application/octet-stream'  # same as unknown types

except ImportError:
    import mimetypes
    log.debug("Using mimetypes from Standard Library")

    def mimetype(filepath:str) -> str:
        """Return the guessed mimetype of a file based on its extension.

        Return 'application/octet-stream' for unknown types and extensionless paths.
        """
        return (mimetypes.guess_type(filepath, strict=False)[0]
                or 'application/octet-stream')


# Most common video file extensions, not meant as a complete list.
# For performance reasons only, to avoid a perhaps expensive mimetype detection
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/DevReadFirst#Videofilesextensions

# Either Gio, Stdlib or both consider a video (mimetype == 'video/...')
VIDEO_EXTENSIONS = [
    '3g2', '3gp', '3gp2', '3gpp', 'asf', 'asx', 'avi', 'divx', 'dv', 'flc',
    'fli', 'flv', 'gvp', 'm1v', 'm2ts', 'm4v', 'mkv', 'moov', 'mov', 'movie',
    'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mxf', 'nsv', 'ogm', 'ogv', 'qt', 'ram',
    'rm', 'rmvb', 'swf', 'ts', 'viv', 'vivo', 'vob', 'wm', 'wmv', 'wmx', 'wvx',
]
# Other extensions included in opensubtitles.org list, sans 'ps'
VIDEO_EXTENSIONS_EXTRA = [
    '60d', 'ajp', 'avchd', 'bik', 'bix', 'box', 'cam', 'dat', 'dmf', 'dvr-ms',
    'evo', 'flic', 'flx', 'gvi', 'h264', 'm2p', 'm2v', 'm4e', 'mjp', 'mjpeg',
    'mjpg', 'movhd', 'movx', 'mpv2', 'nut', 'omf', 'vfw', 'vid', 'video', 'vro',
    'wrap', 'wx', 'x264', 'xvid',
]


class ArchiveFile:
    """Wrapper class to handle both RAR and ZIP files transparently"""
    def __new__(cls, file):
        if   rarfile.is_rarfile(file): return rarfile.RarFile(file, mode='r')
        elif zipfile.is_zipfile(file): return zipfile.ZipFile(file, mode='r')
        raise u.LegendasTVError("Unsupported archive format, must be RAR or ZIP: %s", file)


def extract_archive(archive:   str,
                    path:      str  = None,
                    extlist:   list = None,
                    keep:      bool = True,
                    cached:    bool = True,
                    safe:      bool = True,
                    recursion: int  = 1,
                    _root:     bool = True) -> list:
    """Extract files from an archive and return the list of extracted files.

    <archive>   Input archive file path. Supported formats are ZIP and RAR.
    <path>      Extraction directory, by default the archive path without extension.
                  A blank <path> ("") extracts to the current directory.
    <extlist>   List or a comma-separated string of file extensions (excluding the '.')
                  to filter the extracted list output. By default list all files.
                  Note this just affects the list output, not the extraction itself,
                  which is performed on all files and only affected by <safe>.
    <keep>      Do not delete <archive> after succesful extraction. Default True.
    <cached>    If <path> exists, do not perform actual extraction and consider all files
                  as already extracted. Does not check if files actually exist in <path>,
                  and perform usual <extlist> filtering on output. Default True.
    <safe>      Do not extract files with internal paths containing references to parent
                  directories ('..') or starting with '/' (absolute paths), which could
                  lead to extracted files outside <path>. Default True.
    <recursion> Recursively extract archives found inside <archive> up to a maximum
                  of <recursion> archives. Note <recursion> does not mean recursion depth,
                  but the number of inner archives extracted in any depth.
                  Negative <recursion> do not limit extraction, a dangerous value which
                  might lead to extraction bombs. Zero disables recursive extraction.
                  Default 1.

    Return a list of files after extraction, with their paths, filtered by <extlist>.
    """

    try:
        af = ArchiveFile(archive)
    except u.LegendasTVError as e:
        log.error(e)
        return []

    names = af.namelist()
    log.debug("%d files in archive: %s\n%s",
              len(names), archive, pprint.pformat(names, indent=4))

    if isinstance(extlist, str):
        extlist = extlist.split(',')
    log.debug("extlist = %r", extlist)  # @@

    if safe:
        for name in names[:]:
            if name.startswith('/') or name.startswith('../') or '/../' in name:
                log.warning("Not extracting file with unsafe path in archive %r: %s",
                            archive, name)
                names.remove(name)

    if path is None:
        path = os.path.splitext(archive)[0]
    log.debug("path = %r", path)  # @@

    if cached and os.path.exists(path):
        log.debug("Using already extracted files at: %s", path)
    else:
        log.debug("Extracting to: %s", path)
        os.makedirs(path, exist_ok=True)
        af.extractall(path, members=names)

    outputfiles = []
    for name in names:
        ext = extension(name)
        filepath = os.path.join(path, name)
        log.debug("filepath = %r", filepath)  # @@

        if not extlist or ext in extlist:
            outputfiles.append(filepath)

        elif recursion and ext in ['zip', 'rar']:
            out, recursion = extract_archive(filepath,
                                             path=None,  # derive from filepath
                                             extlist=extlist,
                                             keep=keep,
                                             cached=cached,
                                             safe=safe,
                                             recursion=recursion-1,
                                             _root=False)
            outputfiles.extend(out)

    if hasattr(af, 'close'):
        af.close()

    if not keep:
        try:
            os.remove(archive)
        except FileNotFoundError:
            pass
        except PermissionError as e:
            log.error(e)

    log.info("%d extracted files in '%s', filtered by %s\n%s",
             len(outputfiles), archive, extlist, pprint.pformat(outputfiles, indent=4))

    if not _root:
        return outputfiles, recursion

    return outputfiles


def extension(filepath:str) -> str:
    """Return the normalized filename extension: lowercase without leading dot

    Can be empty. Does not consider POSIX hidden files to be extensions.
    Example: extension('A.JPG') -> 'jpg'
    """
    return os.path.splitext(filepath)[1][1:].lower()


def is_video(filepath:str, strict:bool=True) -> bool:
    """Return True if filepath should be considered a video file.

    Determined by file extension and possibly its guessed mimetype.
    """
    ext = extension(filepath)

    if ext in VIDEO_EXTENSIONS or (not strict and ext in VIDEO_EXTENSIONS_EXTRA):
        return True

    return mimetype(filepath).split('/')[0] == 'video'


def video_hash(filepath:str) -> str:
    """Return the OpenSubtitles video file hash.

    https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
    """
    block = 65536
    fmt = f"<{block//8}Q"  # 8 bytes * 8KiB (unsigned long long)
    vhash = os.path.getsize(filepath) # initial value for hash is file size

    def partialhash(f):
        return sum(struct.unpack(fmt, f.read(block)))

    with open(filepath, "rb") as f:
        try:
            vhash += partialhash(f)
            f.seek(-block, os.SEEK_END)
            vhash += partialhash(f)
            vhash &= 0xFFFFFFFFFFFFFFFF  # cap at 64bit
        except (IOError, struct.error):
            raise u.LegendasTVError("File must be at least %d bytes to hash: %s",
                                    block, filepath)
    return f"{vhash:016x}"


def guess_info(filename:str) -> dict:
    return guessit.guessit(filename)
