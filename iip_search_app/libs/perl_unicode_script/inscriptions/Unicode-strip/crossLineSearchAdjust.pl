#! /usr/bin/perl
use strict;

sub trim($) {
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
}

sub ltrim($) {
	my $string = shift;
	$string =~ s/^\s+//;
	return $string;
}

sub rtrim($) {
	my $string = shift;
	$string =~ s/\s+$//;
	return $string;
}

sub rtrimreturn($) {
	my $string = shift;
	$string =~ s/\n//;
	return $string;
}

foreach my $file (@ARGV) {
	my $bak = $file.".bak";
	system "mv $file $bak";

	open BAK, "<$bak";
	open NEW, ">$file";

	my $inTrans = 0;
	my $buf = "";
	while(<BAK>) {
		if(/\<div.*xml:lang\s*=\s*\"heb\".*\>/ or
				/\<span.*xml:lang\s*=\s*\"heb\".*\>/) { # Hebrew div or span: do nothing
			print NEW;
		} else {
			$_ = ltrim(rtrimreturn($_));
			$_ =~ s/\<lb\s*break\s*=\b*\"no\"\s*\/\>\s*//; # remove word break
			$_ =~ s/\<lb\s*\/\>\s*/ /; # remove line break
			print NEW;
		}
	}
	close BAK;
	close NEW;
	system "rm $bak";
}


