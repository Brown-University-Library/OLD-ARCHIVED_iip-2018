#! /usr/bin/perl
use strict;

my $len = @ARGV;
if($len == 0) {
	print "usage: strip.pl days\n";
	exit;
}

print "Cleaning up...\n";
system("rm ./Copied/*.xml");
system("rm ./Cloned/*.xml");
system("rm ./Decomposed/*.xml");
system("rm ./Stripped/*.xml");
system("rm ./Final/*.xml");
print "Cleaning up done!\n";

system "find ../xml/ -name '*.xml' -mtime -@ARGV[0] -exec cp {} Copied/ \\;" ;

print "Hebrew adjust start...\n";
system("./HebrewAdjust.pl Copied/*.xml");

print "clone start...\n";
system("./clone.bash Copied/*.xml");

print "cross line search adjust start...\n";
system("./crossLineSearchAdjust.pl Cloned/*.xml");

# print "decompose start...\n";
# system("./decompose_zz.bash");

# print "removeDiacritics start...\n";
# system("./removeDiacritics.bash Decomposed/*");

print "finalMerge start...\n";
system("./finalMerge.bash ../xml/*.xml");

#system("rm ../xml_munged/*");
system("cp Final/* ../xml_munged");


