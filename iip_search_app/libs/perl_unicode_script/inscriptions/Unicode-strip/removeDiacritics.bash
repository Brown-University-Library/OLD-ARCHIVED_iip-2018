#! /bin/bash

# $Header: /www/htdocs/projects/Inscriptions/Search/Unicode-strip/RCS/removeDiacritics.bash,v 1.2 2004-06-08 12:53:57-04 cmah Exp $
#

# format:
#	$0 files
# function:
#	execute removeDiacriticsFinal.perl on each "real" file in files
#	a "real" file is one 
#		* that is non-empty
#		* that is not a directory
#		* to which you have write-access
#		* that does not end in "#" or "~"
#		* that is under RCS control
#		* that is not already checked-out
#		
# RCS-maintained logfile near bottom of file
# 

#
# get my own name and path
#
mypath=${0%/*}
myname=${0##/*/}

echo "mypath==$mypath"
	echo "myname==$myname"
#
# process each subsequent file
#
for filepath in "$@"; do
    #
    # separate path from filename
    #
    path=${filepath%/*}
    file=${filepath##/*/}
	if [ $file = $filepath ]; then file=${filepath##*/}
	fi
	name=${file%.*}
    #
    # 
    if [ $path = $file ]; then path="."
    fi
    if   [ -z "$filepath" ]; then
	echo "$myname warning: $filepath is empty, ignoring it"
    elif [ -d "$filepath" ]; then
	echo "$myname warning: $filepath is a directory, I need a file; ignoring it"
    elif [ ! -e "$filepath" ]; then
	echo "$myname warning: $filepath does not exist; ignoring it"
    elif [ ! ${filepath%#} = ${filepath%\~} ]; then 
	echo "$myname warning: $filepath ends in # or ~; ignoring it"
    else
#		echo "$filepath boils down to:"
#		echo "   $path"
#		echo "   $file"
#		echo "   $name"
		echo $filepath > Stripped/$name.stripped.xml

    fi
    done

#
# Written by Syd Bauman (Syd_Bauman@brown.edu)
# 
# With modifications by Carole E. Mah (Carole_Mah@brown.edu)
# 
# $Log: removeDiacritics.bash,v $
# Revision 1.2  2004-06-08 12:53:57-04  cmah
# oops, removed old line of code
#
# Revision 1.1  2004-06-08 12:53:37-04  cmah
# Initial revision
#
# 
# 1999-07-20 begun, based on find-LABEL-in-LG-pckg01.bash (it was based on glob-change-02)
#
