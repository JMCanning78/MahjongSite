#!/bin/sh

if [ $# -eq 0 ] ; then
  find static/js \( -name "*.js" -and -not -iname '*.min.js' \) -exec \
    js-beautify -tnr --brace-style=end-expand {} \;
else
	js-beautify -tnr --brace-style=end-expand $*
fi

