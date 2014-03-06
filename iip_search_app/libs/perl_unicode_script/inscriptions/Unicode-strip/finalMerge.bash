#! /bin/bash

# $Header: /www/htdocs/projects/Inscriptions/Search/Admin/Unicode-strip/RCS/finalMerge.bash,v 1.2 2006-07-12 14:55:41-04 sbauman Exp sbauman $
#

# format:
#	$0 files
# function:
#	execute copy.xsl with 'filename' parameter set on each "real" file in files
#	a "real" file is one 
#		* that is non-empty
#		* that is not a directory
#		* whose name ends in ".xml"
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
echo -n "pwd==";pwd

#
# process each subsequent file
#
for filepath in "$@"; do
    base=`basename $filepath '.xml'`
    if   [ -z "$filepath" ]; then
	echo "$myname warning: $filepath is empty, ignoring it"
    elif [ -d "$filepath" ]; then
	echo "$myname warning: $filepath is a directory, I need a file; ignoring it"
    elif [ ! -e "$filepath" ]; then
	echo "$myname warning: $filepath does not exist; ignoring it"
    elif [ ! ${filepath##*.} = 'xml' ]; then 
	echo "$myname warning: $filepath does not end in 'xml'; ignoring it"
    else
	xsltproc --stringparam filename "Stripped/$base.cloned.decomposed.stripped.xml" \
	    copy.xsl \
	    $filepath  \
	    > Final/$base.xml
#	/opt/local/java/bin/java -jar /opt/local/saxon/saxon8.jar \
#	    -o Final/$base.xml \
#	    $filepath \
#	    copy.xsl "filename=Stripped/$base.cloned.decomposed.stripped.xml"
    fi
    done


# Written by Syd Bauman (Syd_Bauman@brown.edu) at the request of Paul
# Caton, heavily based on Carole Mah's `incorporate.bash` in the same
# directory, which itself is based on stuff I did.

# $Log: finalMerge.bash,v $
# Revision 1.2  2006-07-12 14:55:41-04  sbauman
# First attempt.
#

