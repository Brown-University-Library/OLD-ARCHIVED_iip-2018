#!/usr/bin/env perl

use English;

while (<>) {
    chomp $ARG;
    @list = split ( //, $ARG );
    foreach $char ( @list ) {
	$n = ord($char);
	$x = sprintf "%X", $n;
	$o = sprintf "%o", $n;
	print "$char == $n == x$x == \\$o\n";
    }
}

exit 0;
