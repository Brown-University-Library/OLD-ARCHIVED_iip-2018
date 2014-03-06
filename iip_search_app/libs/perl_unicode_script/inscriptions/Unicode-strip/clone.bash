#! /bin/bash
# $Header: /www/htdocs/projects/Inscriptions/Search/Unicode-strip/RCS/clone.bash,v 1.1 2004-05-25 12:09:49-04 cmah Exp cmah $
#
# format:
#	$0 files
# function:
#	execute cloneDivToNewFile.xsl on each XML file in files
#		
# RCS-maintained logfile near bottom of file
# 

#
# get my own name and path
#
mypath=${0%/*}
myname=${0##/*/}

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

                xsltproc -o Cloned/$name.cloned.xml cloneDivToNewFile.xsl $filepath 
    fi
    done
