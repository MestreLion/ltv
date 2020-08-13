UnRAR support on Python
===============================================================================

`unrar` - A ctypes wrapper for UnRAR library
--------------------------------------------
- Source Code: https://github.com/matiasb/python-unrar
- License: GPLv3
- PyPi: `unrar`
- Debian: -

Notes:

- Require external library `libunrar.so` or equivalent
- Library is found via `ctypes.util.find_library("unrar")` or set by `$UNRAR_LIB_PATH`
- Pythonic API, compatible with ZipFile
- Great documentation: https://python-unrar.readthedocs.org
- `pip` does not install external library

**Veredict**: _Supported_, preferable choice. `libunrar.so` can be compiled,
but unlikely to be already installed.


`rarfile` - Python module for RAR archive reading
--------------------------------------------------
- Source code / Website:  https://github.com/markokr/rarfile
- License: ISC (equivalent to MIT)
- PyPi: `rarfile`
- Debian: `python3-rarfile`, from source package `python-rarfile`

Notes:

- Require external executable, either `unrar`, `unar` or `bsdtar`, on `$PATH`
- Pythonic API, compatible with ZipFile
- `pip` does not install external executable
- `apt` pulls both `unrar-free` and `bsdtar`

**Veredict**: _Supported_. `unrar` can be compiled and might be already installed.


`unrardll` - Python wrapper for the UnRAR DLL
---------------------------------------------
- Source code / Website: https://github.com/kovidgoyal/unrardll
- License: BSD 3-Clause
- PyPi: `unrardll`
- Debian: `python3-unrardll`, from source package `unrardll` (Ubuntu 19.10+)

Notes:

- Require compiled CPython module using external UnRAR C++ headers
- Poor documentation and un-pythonic API
- Contains a CI script in Python to download, extract and build official C++ sources
- `pip` install fails if C++ headers not installed (from Debian's `unrarlib-dev`)
- `apt` pulls `libunrar-dev` on build and `libunrar5` on install.

**Veredict**: _**Not** supported_. Completely alien API for no benefit over `unrar` module.


Debian / Ubuntu source packages for UnRAR
===============================================================================

`unrar-nonfree`
---------------
- Upstream is official [RARLab](https://www.rarlab.com/rar_add.htm)
- Builds:
    - `unrar`,        executable `/usr/bin/unrar-nonfree` (symlinked to `/usr/bin/unrar`)
    - `libunrar-dev`, library    `/usr/lib/x86_64-linux-gnu/libunrar.so`   (Ubuntu 19.10+)
    - `lubunrar5`,    library    `/usr/lib/x86_64-linux-gnu/libunrar.so.5` (Ubuntu 19.10+)


`unrar-free`
------------
- Independent, free source
- Upstream seems dead: website is down, no releases since 2014
- Lacks features: no RAR5, and RAR3 requires external `unar` (The UnArchiver)
- Builds:
    - `unrar-free`,   executable `/usr/bin/unrar-free` (symlinked to `/usr/bin/unrar`)
