#! /usr/bin/perl
use strict;

my $len = @ARGV;
if($len == 0) {
	print "usage: strip.pl days\n";
	exit;
}

print "Cleaning up...\n";
system("rm ./Copied/*");
system("rm ./Cloned/*");
system("rm ./Decomposed/*");
system("rm ./Stripped/*");
system("rm ./Final/*");
print "Cleaning up done!\n";

system "find ../xml/ -name '*.xml' -mtime -@ARGV[0] -exec cp {} Copied/ \\;" ;

print "Hebrew adjust start...\n";
system("./HebrewAdjust.pl Copied/*");

print "clone start...\n";
system("./clone.bash Copied/*");

print "cross line search adjust start...\n";
system("./crossLineSearchAdjust.pl Cloned/*");

print "decompose start...\n";
system("./decompose_zz.bash");

print "removeDiacritics start...\n";
system("./removeDiacritics.bash Decomposed/*");

print "finalMerge start...\n";
system("./finalMerge.bash Copied/*.xml");

#system("rm ../xml_munged/*");
system("cp Final/* ../xml_munged");


