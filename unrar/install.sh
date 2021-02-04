#!/bin/bash -eu
#
# UnRAR application and library installer
#
# Copyright (C) 2019 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

# See "UnRAR source" at https://www.rarlab.com/rar_add.htm
url=https://www.rarlab.com/rar/unrarsrc-5.9.4.tar.gz
tardir=unrar-5.9.4
libname=libunrar.so
exename=unrar

#############

mydir=$(dirname "$(readlink -f "$0")")
archive=$mydir/$(basename "$url")
tardir=$mydir/$tardir

case "$1" in
	-h|--help) echo "Usage: ./install.sh [-h|--help] [--clean]"; exit;;
	--clean) rm -rf -- "$tardir" "$archive" "$mydir"/{"$exename","$libname"}; exit;;
esac


wget --timestamping --directory-prefix "$mydir" -- "$url"
rm -rf -- "$tardir"
mkdir -vp -- "$tardir"

tar --extract --file "$archive" --strip-components=1 --directory "$tardir"

cd "$tardir"

make unrar && cp -v --update  -- "$exename" "$mydir"
make lib   && cp -v --update  -- "$libname" "$mydir"

printf '\nexport UNRAR_LIB_PATH=%q\n' "$mydir"/"$libname"
