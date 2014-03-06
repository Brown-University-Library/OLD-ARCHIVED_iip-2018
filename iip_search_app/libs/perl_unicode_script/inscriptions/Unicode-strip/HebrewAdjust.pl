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
		if(/\<div.*xml:lang\s*=\s*\"heb\".*\>/) { # a Hebrew div is found
			if(! /\<\/div\>/) { # if the end-div is not in the same line
				$inTrans = 1;
			}
		} elsif(/\<span.*xml:lang\s*=\s*\"heb\".*\>/) { # a Hebrew span is found
			if(! /\<\/span\>/) { # if the end-span is not in the same line
				$inTrans = 2;	
			}
		} elsif($inTrans == 1 && /\<\/div\>/) {
			$inTrans = 0;
		} elsif($inTrans == 2 && /\<\/span\>/) {
			$inTrans = 0;
		}

		if($inTrans == 0) {
			if(length($buf) == 0) {
				print NEW;
			} else {
				$buf .= ltrim(rtrimreturn($_));
				print NEW "$buf\n";
				$buf = "";
			}
		} else {
			$buf .= ltrim(rtrimreturn($_));
		}

	}
	close BAK;
	close NEW;
	system "rm $bak";
}


