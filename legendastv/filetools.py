# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Assorted file-related tools
"""

import logging
import pprint
import os
import shutil
import struct

import guessit

from . import util as u
from . import rarcompat


# Declared before imports are done so alternatives can be logged
log = logging.getLogger(__name__)


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


def extract_archive(archive:   str,
                    path:      str  = None,
                    extlist:   list = None,
                    keep:      bool = True,
                    overwrite: bool = False,
                    safe:      bool = True,
                    recursion: int  = 1,
                    _root:     bool = True) -> list:
    """Extract files from an archive and return the list of extracted files.

    <archive>   Input archive file path. Supported formats are ZIP and RAR.
    <path>      Extraction directory, by default the archive path without extension.
                  A blank <path> ("") extracts to the current directory.
    <extlist>   List or a comma-separated string of file extensions (excluding the '.')
                  to filter the extracted files. By default extract all files except
                  the ones excluded by <safe>, if any.
    <keep>      Do not delete <archive> after succesful extraction. Default True.
    <overwrite> Force extraction of files that are already present in their final
                  destination path. Does not check if files actually have same content.
                  Default False.
    <safe>      Do not extract files with internal paths containing references to parent
                  directories ('..') or starting with '/' (absolute paths), which could
                  lead to extracted files outside <path>. Default True.
    <recursion> Recursively extract archives found inside <archive> up to a maximum
                  of <recursion> archives. Note <recursion> does not mean recursion depth,
                  but the number of inner archives extracted in any depth. Extract them
                  "in-place", with their <path> set to None. The archives themselves and
                  their contents are listed on final output subject to <extlist> rules.
                  Negative <recursion> do not limit extraction, a dangerous value which
                  might lead to extraction bombs. Zero disables recursive extraction.
                  Default 1.

    Return a list of files after extraction, with their paths, filtered by <extlist>.
    """
    try:
        af = rarcompat.ArchiveFile(archive)
    except u.LegendasTVError as e:
        log.error(e)
        if not _root:
            return [], recursion
        return []

    if path is None:
        path = os.path.splitext(archive)[0]
    log.debug("Extracting archive to %r: %s", path, archive)

    names = af.namelist()
    log.debug("%d files in archive:\n%s", len(names), pprint.pformat(names, indent=4))

    if isinstance(extlist, str):
        extlist = extlist.split(',')

    # List of files to be extracted
    members = []
    archives = recursion
    for name in names[:]:
        if safe and (name.startswith('/') or name.startswith('../') or '/../' in name):
            log.warning("Not extracting file with unsafe path in archive %r: %s",
                        archive, name)
            names.remove(name)
            continue
        if not overwrite and os.path.exists(os.path.join(path, name)):  # racy but fine
            continue
        ext = extension(name)
        if not extlist or ext in extlist:
            members.append(name)
            continue
        if archives and ext in ('zip', 'rar'):
            members.append(name)
            archives -= 1
            continue

    if members:
        remove = makedirs(path)
        try:
            af.extractall(path, members=members)
            remove = False
        finally:
            if remove:
                try:
                    os.removedirs(path)
                except OSError:
                    pass

    outputfiles = []
    for name in names:
        filepath = os.path.join(path, name)
        ext = extension(filepath)

        if not extlist or ext in extlist:
            outputfiles.append(filepath)

        if recursion and ext in ('zip', 'rar'):
            out, recursion = extract_archive(filepath,
                                             path=None,  # derive from filepath
                                             extlist=extlist,
                                             keep=keep,
                                             overwrite=overwrite,
                                             safe=safe,
                                             recursion=recursion-1,
                                             _root=False)
            outputfiles.extend(out)

    if not keep:
        try:
            os.remove(archive)
        except FileNotFoundError:
            pass
        except PermissionError as e:
            log.error(e)

    if not _root:
        return outputfiles, recursion

    return outputfiles


def rename_srt(srtpath, videopath):
    """Copy an SRT file to the same dir as a Video file, also renaming to match it"""
    try:
        return shutil.copyfile(srtpath, "{}.srt".format(os.path.splitext(videopath)[0]))
    except shutil.SameFileError:
        return srtpath


def makedirs(path:str):
    """Create leaf and all intermediate directories in <path>.

    Return True if <path> is actually created now, False if it already exists.
    Raise LegendasTVError on OSError exceptions (tipically permission / access errors)
    """
    try:
        os.makedirs(path)
        return True
    except FileExistsError:
        return False
    except OSError as e:
        raise u.LegendasTVError("Error creating path '%r': %s", path, e)


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
