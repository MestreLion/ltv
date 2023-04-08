#!/bin/bash
if [[ -z "$1" ]] || [[ "$1" == '-h' ]] || [[ "$1" == '--help' ]]; then
	echo "Download de legendas no Legendei.to"
	echo "Usage: ${0##*/} BUSCA"
fi
search=$1
wget -4 -O - -- "https://legendei.to/${search}/" | grep '/oficial' | cut -d\" -f4 | wget -4 -i- -O "$search".zip
