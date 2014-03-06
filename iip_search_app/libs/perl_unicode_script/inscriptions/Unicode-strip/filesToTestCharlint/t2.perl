#!/usr/bin/env perl

use English;

open(INFILE, "<$ARGV[0]");
binmode(INFILE, ":raw");

while (<INFILE>) {
    chomp $ARG;
    @list = split ( //, $ARG );
    foreach $char ( @list ) {
	$n = ord($char);
	$x = sprintf "%X", $n;
	$o = sprintf "%o", $n;
	print "$char == $n == x$x == \\$o\n";
    }
}

close INFILE;

exit 0;
