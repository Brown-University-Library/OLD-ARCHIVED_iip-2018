#! /usr/bin/perl


use English;
use Encode;
use Unicode::Normalize;

use encoding "utf8";

my $newVersion;

binmode(STDOUT, ":utf8");

while (<STDIN>) {
  
    # http://ptolemy.tlg.uci.edu/~opoudjis/unicode/unicode_gkbkgd.html#titlecase

    $newVersion = $_;

    $newVersion =~ s/\x{0300}//g;
    $newVersion =~ s/\x{0301}//g;
    $newVersion =~ s/\x{0342}//g;
    $newVersion =~ s/\x{0314}//g;
    $newVersion =~ s/\x{0313}//g;
    $newVersion =~ s/\x{0345}//g;
    $newVersion =~ s/\x{0308}//g;
    $newVersion =~ s/\x{0304}//g;
    $newVersion =~ s/\x{0306}//g;
    $newVersion =~ s/\x{1FFD}//g;
    $newVersion =~ s/\x{0303}//g;

    print $newVersion;

}




exit;

