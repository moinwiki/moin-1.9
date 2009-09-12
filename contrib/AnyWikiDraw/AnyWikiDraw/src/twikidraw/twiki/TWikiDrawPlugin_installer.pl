# Install script for TWikiDrawPlugin
#
# Copyright (C) 2004 Crawford Currie http://c-dot.co.uk
#
# NOTE TO THE DEVELOPER: THIS FILE IS GENERATED AUTOMATICALLY
# BY THE BUILD PROCESS DO NOT EDIT IT - IT WILL BE OVERWRITTEN
#
use strict;
use Socket;

# The root of package URLs
my $PACKAGES_URL = "http://www.twiki.org/p/pub/Plugins/";

my $noconfirm = 0;
my $twiki;
my $NL = "\n";
my %manifest = ( 'data/TWiki/TWikiDrawPlugin.txt'=>508,'lib/TWiki/Plugins/TWikiDrawPlugin.pm'=>508,'lib/TWiki/Plugins/TWikiDrawPlugin/source.zip'=>508,'pub/TWiki/TWikiDrawPlugin/ATEXT1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ATEXT2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ATEXT3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/BORDDEC1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/BORDDEC2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/BORDDEC3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/CONN1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/CONN2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/CONN3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/DIAMOND2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/DIAMOND3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ELLIPSE1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ELLIPSE2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ELLIPSE3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ERASER2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/ERASER3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/example.draw'=>508,'pub/TWiki/TWikiDrawPlugin/example.map'=>508,'pub/TWiki/TWikiDrawPlugin/example.gif'=>508,'pub/TWiki/TWikiDrawPlugin/LINE1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/LINE2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/LINE3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/OCONN1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/OCONN2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/OCONN3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/PERT2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/PERT3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/POLYGON1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/POLYGON2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/POLYGON3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/RECT1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/RECT2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/RECT3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/RRECT1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/RRECT2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/RRECT3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/SCRIBBL1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/SCRIBBL2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/SCRIBBL3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/SEL1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/SEL2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/SEL3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TEXT1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TEXT2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TEXT3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TOBACK2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TOBACK3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TOFRONT2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TOFRONT3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TRIANGLE2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/TRIANGLE3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/URL1.gif'=>508,'pub/TWiki/TWikiDrawPlugin/URL2.gif'=>508,'pub/TWiki/TWikiDrawPlugin/URL3.gif'=>508,'pub/TWiki/TWikiDrawPlugin/screenshot.png'=>508,'pub/TWiki/TWikiDrawPlugin/twikidraw.jar'=>508,'templates/twikidraw.tmpl'=>508,'templates/twikidraw.pattern.tmpl'=>508, );
my @deps = (  );
my $dakar;
my %available;
my $lwp;
my @archTypes = ( 'tar.gz', 'tgz', 'zip' );

require 5.006;

BEGIN {
    my $check_perl_module = sub {
        my $module = shift;

        eval "use $module;";
        if( $@ ) {
            print "Warning: $module is not available, some installer functions have been disabled\n";
            $available{$module} = 0;
        } else {
            $available{$module} = 1;
        }
        return $available{$module};
    };

    unless ( -d 'lib' &&
             -d 'bin' &&
             -e 'bin/setlib.cfg' ) {
        die 'This installer must be run from the root directory of a TWiki installation';
    }
    my $here = `pwd`; # in case bin is a link
    # read setlib.cfg
    chdir('bin');
    require 'setlib.cfg';
    chomp($here); chdir($here);
    # See if we can make a TWiki. If we can, then we can save topic
    # and attachment histories. Key off TWiki::Merge because it was
    # added in Dakar.
    if( &$check_perl_module( 'TWiki::Merge' )) {
        eval "use TWiki";
        $twiki = new TWiki();
        $dakar = 1;
    } else {
        # Not Dakar
        no strict;
        do 'lib/TWiki.cfg';
        if( -e 'lib/LocalSite.cfg') {
            # Store plugin config in LocalSite.cfg
            do 'lib/LocalSite.cfg';
        }
        use strict;
        $dakar = 0;
    }

    if( &$check_perl_module( 'LWP' )) {
        $lwp = new LWP::UserAgent();
        $lwp->agent("TWikiPluginsInstaller");
    }
    &$check_perl_module( 'CPAN' );
}

sub check_dep {
    my $dep = shift;
    my( $ok, $msg ) = (1, '');

    if( $dep->{type} =~ /^(perl|cpan)$/i ) {
        # Try to 'use' the perl module
        eval 'use '.$dep->{name};
        if( $@ ) {
            $msg = $@;
            $msg =~ s/ in .*$/\n/s;
            $ok = 0;
        } else {
            # OK, it was loaded. See if a version constraint is specified
            if( defined( $dep->{version} ) ) {
                my $ver;
                # check the $VERSION variable in the loaded module
                eval '$ver = $'.$dep->{name}.'::VERSION;';
                if( $@ || !defined( $ver ) ) {
                    $msg .= 'The VERSION of the package could not be found: '.
                      $@;
                    $ok = 0;
                } else {
                    # The version variable exists. Clean it up
                    $ver =~ s/^.*\$Rev: (\d+)\$.*$/$1/;
                    $ver =~ s/[^\d]//g;
                    $ver ||= 0;
                    eval '$ok = ( $ver '.$dep->{version}.' )';
                    if( $@ || ! $ok ) {
                        # The version variable fails the constraint
                        $msg .= ' '.$ver.' is currently installed: '.$@;
                        $ok = 0;
                    }
                }
            }
        }
    } else {
        # This module has no perl interface, and can't be checked
        $ok = 0;
        $msg = 'Module is type '.$dep->{type}.
          ', and cannot be automatically checked.'.$NL.
            'Please check it manually and install if necessary.'.$NL;
    }
    return ( $ok, $msg );
}

# Satisfy dependencies on modules, by checking:
# 1. If the module is a perl module, then:
#    1. If the module is loadable in the current environment
#    2. If the dependency has specified a version constraint, then
#       the module must have a top-level variable VERSION which satisfies
#       the constraint.
#       Note that all TWiki modules are perl modules - even non-perl
#       distributions have a perl 'stub' module that carries the version info.
# 2. If the module is _not_ perl, then we can't check it.
sub satisfy {
    my $dep = shift;
    my $result = 1;
    my $trig = eval $dep->{trigger};

    return 1 unless ( $trig );

    print <<DONE;
##########################################################
Checking dependency on $dep->{name}....
DONE
    my ( $ok, $msg ) = check_dep( $dep );

    unless ( $ok ) {
        print <<DONE;
*** TWikiDrawPlugin depends on $dep->{type} package $dep->{name} $dep->{version}
which is described as "$dep->{description}"
But when I tried to find it I got this error:

$msg
DONE
        $result = 0;
    }

    unless( $ok ) {
        if( $dep->{name} =~ m/^TWiki::(Contrib|Plugins)::(\w*)/ ) {
            my $pack = $1;
            my $packname = $2;
            $packname .= $pack if( $pack eq 'Contrib' && $packname !~ /Contrib$/);
            my $reply = ask('Would you like me to try to download and install the latest version of '.$packname.' from twiki.org?');
            if( $reply ) {
                $result = installPackage( "$PACKAGES_URL/$packname/", $packname );
            }
        } elsif ( $dep->{type} eq 'cpan' && $available{CPAN} ) {
            print <<'DONE';
This module is available from the CPAN archive (http://www.cpan.org). You
can download and install it from here. The module will be installed
to wherever you configured CPAN to install to.

DONE
            my $reply = ask('Would you like me to try to download and install the latest version of '.$dep->{name}.' from cpan.org?');
            if( $reply ) {
                CPAN::install( $dep->{name} );
                ( $ok, $msg ) = check_dep( $dep );
                unless( $ok ) {
                    my $e = "it";
                    if( $CPAN::Config->{makepl_arg} =~ /PREFIX=(\S+)/) {
                        $e = $1;
                    }
                    print STDERR <<DONE;
#########################################################################
# WARNING: I still can't find the module $dep->{name}
#
# If you installed the module in a non-standard directory, make sure you
# have followed the instructions in bin/setlib.cfg and added $e
# to your \@INC path.
#########################################################################

DONE
                }
            }
        }
    }

    return $result;
}

=pod

---++ StaticMethod ask( $question ) -> $boolean
Ask a question.
Example: =if( ask( "Proceed?" ))

=cut

sub ask {
    my $q = shift;
    my $reply;

    return 1 if $noconfirm;

    $q .= '?' unless $q =~ /\?\s*$/;

    print $q.' [y/n] ';
    while ( ( $reply = <STDIN> ) !~ /^[yn]/i ) {
        print 'Please answer yes or no'.$NL;
    }
    return ( $reply =~ /^y/i ) ? 1 : 0;
}

=pod

---++ StaticMethod prompt( $question, $default ) -> $string
Prompt for a string, using a default if return is pressed.
Example: =$dir = prompt("Directory");

=cut

sub prompt {
    my( $q, $default) = @_;
    my $reply = '';
    while( !$reply ) {
        print $q;
        print " ($default)" if defined $default;
        print ': ';
        $reply = <STDIN>;
        chomp($reply);
        $reply ||= $default;
    }
    return $reply;
}

=pod

---++ StaticMethod getConfig( $major, $minor, $cairo ) -> $string
   * =$major= name of major key.
   * =$minor= if undefined, there is no minor key
   * =$cairo= expression that when evaled will get the cairo style config var
Get the value of a config var, trying first the Dakar option and
then if that fails, the Cairo name (if any).
Example:
=getConfig("Name")=
will get the value of =$TWiki::cfg{Name}=.
=getConfig("MyPlugin", "Name")=
will get the value of =$TWiki::cfg{Name}=.
=getConfig("HomeTopicName", undef, '$mainTopicname')=
will get the name of the WebHome topic on Dakar and Cairo.

See setConfig for more information on major/minor keys.

=cut

sub getConfig {
    my( $major, $minor, $cairo ) = @_;

    if( $minor && defined $TWiki::cfg{$major}{$minor} ) {
        return $TWiki::cfg{$major}{$minor};
    }
    if (!$minor && defined $TWiki::cfg{$major}) {
        return $TWiki::cfg{$major};
    }

    if( defined $cairo ) {
        return eval $cairo;
    }
    return undef;
}

=pod

---++ StaticMethod commentConfig( $comment )
   * $comment - comment to insert in LocalSite.cfg, usually before a setConfig
Inserts a comment into LocalSite.cfg. The comment will usually describe a following setConfig; for example,
<verbatim>
commentConfig( <<HERE
#---++ Cars Plugin
# **STRING 30**
# Name of manufacturer
HERE
);
setConfig( 'CarsPlugin', Manufacturer => 'Mercedes' );
</verbatim>

=cut

sub commentConfig {
    open(F, ">>lib/LocalSite.cfg") ||
              die "Failed to open lib/LocalSite.cfg for write";
    print F $_[0];
    close(F);
}

=pod

---++ StaticMethod setConfig( $major, ... )
   * =$major= if defined, name of major key. If not given, there is no major key and the minorkeys are treated as major keys
   * =...= list of minorkey=>value pairs
Set the given configuration variables in LocalSite.cfg. =$value= must be
complete with all syntactic sugar, including quotes.
The valued are written to $TWiki::cfg{major key}{setting} if a major
key is given (recommended, use the plugin name) or $TWiki::cfg{setting} otherwise. Example:
<verbatim>
setConfig( 'CarsPlugin', Name=>"'Mercedes'" };
setConfig( Tools => "qw(hammer saw screwdriver)" };
</verbatim>
will write
<verbatim>
$TWiki::cfg{CarsPlugin}{Best} = 'Mercedes';
$TWiki::cfg{Tools} = qw(hammer saw screwdriver);
</verbatim>

=cut

sub setConfig {
    my @settings = @_;
    my $txt;
    my $key;
    if (scalar(@settings) % 2) {
        # pluck the first odd parameter off to be the major key
        $key = shift @settings;
    }
    my %keys = @settings;
    if( -e "lib/LocalSite.cfg" ) {
        open(F, "<lib/LocalSite.cfg") ||
          die "Failed to open lib/LocalSite.cfg for read";
        undef $/;
        $txt = <F>;
        close(F);
        $txt =~ s/\n+1;\s*//gs;
        # kill the old settings (and previous comment) if any are there
        foreach my $setting ( keys %keys ) {
            if( $key ) {
                $txt =~ s/(# \*\*.*?\n(#.*?\n))?\$TWiki::cfg{$key}{$setting}\s*=.*;\r?\n//s;
            } else {
                $txt =~ s/(# \*\*.*?\n(#.*?\n))?\$TWiki::cfg{$setting}\s*=.*;\r?\n//s;
            }
        }
    }
    $txt .= "\n" unless $txt =~ /\n$/s;
    open(F, ">lib/LocalSite.cfg") ||
      die "Failed to open lib/LocalSite.cfg for write";
    print F $txt if $txt;
    foreach my $setting ( keys %keys ) {
        if( defined $key ) {
            print F '$TWiki::cfg{'.$key.'}{'.$setting.'} = ';
        } else {
            print F '$TWiki::cfg{'.$setting.'} = ';
        }
        print F $keys{$setting}, ";\n";
    }
    print F "1;\n";
    close(F);

    # is this Cairo or earlier? If it is, we need to include
    # LocalSite.cfg from TWiki.cfg
    unless( $dakar ) {
        open(F, "<lib/TWiki.cfg");
        undef $/;
        $txt = <F>;
        close(F);
        unless( $txt =~ /^do.*LocalSite\.cfg/m ) {
            $txt =~ s/^\s*1\s*;\s*$//m;
            open(F, ">lib/TWiki.cfg") ||
              die "Failed to open lib/TWiki.cfg for write";
            print F "$txt\ndo 'LocalSite.cfg';\n1;\n";
            close(F);
        }
    }
}

# Try and download an archive from a URI
# Return undef if the download failed, or the local filename otherwise
sub getArchive {
    my( $url, $archive ) = @_;

    foreach my $type ( @archTypes ) {
        my $f = $archive.'.'.$type;

        if( -e $f ) {
            my $ans = ask( 'An existing '.$f.
                        ' exists; would you like me to use it?' );
            return $f if $ans;

            unless ( unlink( $f )) {
                print STDERR 'Could not remove old '.$f.$NL;
            }
        }
    }

    my $response;
    foreach my $type ( @archTypes ) {
        $response = $lwp->get( $url.$archive.'.'.$type );

        if( $response->is_success() ) {
            my $f = "$archive.$type";
            open(F, ">$f" ) || die "Failed to open $f for write: $!";
            print F $response->content();
            close(F);
            return $f;
        }
    }

    print STDERR 'Failed to download ', $archive,
      "\n", $response->status_line, $NL;

    return undef;
}

# install a package from the given url
sub installPackage {
    my( $url, $package ) = @_;

    my $file = getArchive( $url, $package );

    return 0 unless $file && unpackArchive( $file );

    if( -e $package.'_installer.pl' ) {
        print `perl ${package}_installer.pl -a install`;
        if ( $? ) {
            print STDERR 'Installation of ',$package,' failed',$NL;
            return 0;
        }
    }

    return 1;
}

=pod

---++ StaticMethod unpackArchive( $archive, $remapper )
Unpack an archive. The unpacking method is determined from the file
extension e.g. .zip, .tgz. .tar, etc.

The remapper is a callback function that is used to rename
target file paths, $remapper( $path ) -> $path. This supports
installations that have renamed their data and pub directories,
for example.

=cut

sub unpackArchive {
    my( $name, $remapper ) = @_;

    if( $name =~ /\.zip/i ) {
        return unzip( $name, $remapper );
    } elsif( $name =~ /(\.tar\.gz|\.tgz|\.tar)/ ) {
        return untar( $name, $remapper );
    } else {
        print STDERR 'Failed to unpack archive ',$name,
          '; unrecognized file type\n';
    }
}

=pod

---++ StaticMethod unzip $archive )
Unzip a zip using Archive::Zip if installed, falling back to
command-line unzip otherwise.

=cut

sub unzip {
    my( $archive, $remapper ) = @_;

    eval 'use Archive::Zip';
    unless ( $@ ) {
        my $zip = new Archive::Zip( $archive );
        unless ( $zip ) {
            print STDERR 'Could not open zip file '.$archive.$NL;
            return 0;
        }

        my @members = $zip->members();
        foreach my $member ( @members ) {
            my $file = $member->fileName();
            my $target = $remapper ? &$remapper( $file ) : $file ;
            my $err = $zip->extractMember( $file, $target );
            if ( $err ) {
                print STDERR 'Failed to extract ',$file,' from zip file ',
                  $zip,'. Archive may be corrupt.',$NL;
                return 0;
            } else {
                print "    $target\n";
            }
        }
    } else {
        print STDERR 'Archive::Zip is not installed; trying unzip'.$NL;
        print `unzip $archive`;
        if ( $! ) {
            print STDERR 'unzip failed: ',$!,$NL;
            return 0;
        }
    }

    return 1;
}

=pod

---++ StaticMethod untar( $archive, $remapper )
Unpack a tar using Archive::Tar if installed, falling back to
command-line tar otherwise.

=cut

sub untar {
    my( $archive, $remapper ) = @_;

    my $compressed = ( $archive =~ /z$/i ) ? 'z' : '';

    eval 'use Archive::Tar';
    unless ( $@ ) {
        my $tar = new Archive::Tar( $archive, $compressed );
        unless ( $tar ) {
            print STDERR 'Could not open tar file '.$archive.$NL;
            return 0;
        }

        my @members = $tar->list_files();
        foreach my $file ( @members ) {
            my $target = $remapper ? &$remapper( $file ) : $file;

            my $err = $tar->extract_file( $file, $target );
            unless ( $err ) {
                print STDERR 'Failed to extract ',$file,' from tar file ',
                  $tar,'. Archive may be corrupt.',$NL;
                return 0;
            } else {
                print "    $target\n";
            }
        }
    } else {
        print STDERR 'Archive::Tar is not installed; trying tar'.$NL;
        print `tar xvf$compressed $archive`;
        if ( $! ) {
            print STDERR 'tar failed: ',$!,$NL;
            return 0;
        }
    }

    return 1;
}

# Check in. On Cairo, do nothing because the apache user
# has everything checked out :-(
sub checkin {
    my( $web, $topic, $file ) = @_;

    # If this is Dakar, we have a good chance of completing the
    # install.
    my $err = 1;
    if( $twiki ) {
        my $user =
          $twiki->{users}->findUser($TWiki::cfg{AdminUserWikiName}, $TWiki::cfg{AdminUserWikiName});
        if( $file ) {
	       print <<DONE;
##########################################################
Adding file: $file to installation ....
(attaching it to $web.$topic)
DONE
          # Need copy of file to upload it, use temporary location
          require File::Copy;
          use File::Copy;
          require File::Temp;
          use File::Temp ();
  		    my $origfile = $TWiki::cfg{PubDir} . '/' . $web . '/' . $topic . '/' . $file;
          my $tmp = new File::Temp( UNLINK => 1 );
          my $tmpfilename = $tmp->filename;
          copy($origfile, $tmpfilename) or die "$origfile could no be copied to tmp dir ($tmpfilename).";
          my @stats = stat $origfile;
          my $fileSize = $stats[7];
          my $fileDate = $stats[9]; 
          $err = $twiki->{store}->saveAttachment
            ( $web, $topic, $file, $user,
	           { comment => 'Saved by install script',
	             file => $tmpfilename, 
                filesize => $fileSize,
                filedate => $fileDate } );
            # Logic in Store.pm unfortunately returns two different codes for attachments and topics
            $err = !$err;
        } else {
	         print <<DONE;
##########################################################
Adding topic: $web.$topic to installation ....
DONE
            # read the topic to recover meta-data
            my( $meta, $text ) =
              $twiki->{store}->readTopic( $user, $web, $topic );
            $err = $twiki->{store}->saveTopic
              ( $user, $web, $topic, $text, $meta,
                { comment => 'Saved by install script' } );
        }
    }
    return ( !$err );
}

sub uninstall {
    my $file;
    my @dead;
    foreach $file ( keys %manifest ) {
        if( -e $file ) {
            push( @dead, $file );
        }
    }
    unless ( $#dead > 1 ) {
        print STDERR 'No part of TWikiDrawPlugin is installed';
        return 0;
    }
    print 'To uninstall TWikiDrawPlugin, the following files will be deleted:'.$NL;
    print join( ', ', @dead );
    my $reply = ask('Are you SURE you want to uninstall TWikiDrawPlugin?');
    if( $reply ) {
        # >>>> PREUNINSTALL
        # No PREUNINSTALL script;
        # <<<< PREUNINSTALL
        foreach $file ( keys %manifest ) {
            if( -e $file ) {
                unlink( $file );
            }
        }
        # >>>> POSTUNINSTALL
        # No POSTUNINSTALL script;
        # <<<< POSTUNINSTALL
    }
    print '### TWikiDrawPlugin uninstalled ###'.$NL;
    return 1;
}

sub install {
    # >>>> PREINSTALL
    # No PREINSTALL script;
    # <<<< PREINSTALL
    unless ( $noconfirm ) {
        print 'Hit <Enter> to proceed with installation',$NL;
        <STDIN>;
    }
    my $unsatisfied = 0;
    foreach my $dep ( @deps ) {
        unless ( satisfy( $dep ) ) {
            $unsatisfied++;
        }
    }

    # For each file in the MANIFEST, set the permissions, and check
    # to see if it is targeted at pub or data. If it is, then add a
    # call to "checkin" for the file.
    my @topic;
    my @pub;
    my @bads;
    my $file;
    foreach $file ( keys %manifest ) {
        if( $file =~ /^data\/(\w+)\/(\w+).txt$/ ) {
            push(@topic, $file);
        } elsif( $file =~ /^pub\/(\w+)\/(\w+)\/([^\/]+)$/ ) {
            push(@pub, $file);
        }
        chmod( $manifest{$file}, $file ) ||
          print STDERR "WARNING: cannot set permissions on $file\n";
    }
    foreach $file ( @topic ) {
        $file =~ /^data\/(\w+)\/(\w+).txt$/;
        unless( checkin( $1, $2, undef )) {
            push( @bads, $file );
        }
    }
    foreach $file ( @pub ) {
        $file =~ /^pub\/(\w+)\/(\w+)\/([^\/]+)$/;
        unless( checkin( $1, $2, $3 )) {
            push( @bads, $file );
        }
    }

    if( scalar( @bads )) {
        print STDERR '
WARNING: I cannot automatically update the local revision history for:',"\n\t";
        print STDERR join( "\n\t", @bads );
        print STDERR <<DONE;

You can update the revision histories of these files by:
   1. Editing any topics and saving them without changing them,
   2. Uploading attachments to the same topics again.
Ignore this warning unless you have modified the files locally.
DONE
    }

    print $NL.'### TWikiDrawPlugin installed';
    print ' with ',$unsatisfied.' unsatisfied dependencies' if ( $unsatisfied );
    print ' ###'.$NL;
    # >>>> POSTINSTALL
    # No POSTINSTALL script;
    # <<<< POSTINSTALL

    print $NL,'### Installation finished ###',$NL;
}

sub usage {
    print STDERR <<'DONE';
Usage:TWikiDrawPlugin_installer [-a] install
      TWikiDrawPlugin_installer [-a] uninstall
      TWikiDrawPlugin_installer [-a] upgrade

Operates on the directory tree below where it is run from,
so should be run from the top level of your TWiki installation.

install will check dependencies and perform any required
post-install steps.

uninstall will remove all files that were installed for
TWikiDrawPlugin even if they have been locally modified.

upgrade will download the latest zip from TWiki.org and install
it, overwriting your existing zip and installer script.

-a means don't prompt for confirmation before resolving
   dependencies

DONE
}

unshift( @INC, 'lib' );

print $NL,'### TWikiDrawPlugin Installer ###',$NL,$NL;
my $n = 0;
my $action = 'install';
while ( $n < scalar( @ARGV ) ) {
    if( $ARGV[$n] eq '-a' ) {
        $noconfirm = 1;
    } elsif( $ARGV[$n] =~ m/(install|uninstall|upgrade)/ ) {
        $action = $1;
    } else {
        usage( );
        die 'Bad parameter '.$ARGV[$n];
    }
    $n++;
}

print <<DONE;
This installer must be run from the root directory of your TWiki
installation.
DONE
unless( $noconfirm ) {
    print <<DONE
    * The script will not do anything without asking you for
      confirmation first.
DONE
}
print <<DONE;
    * You can abort the script at any point and re-run it later
    * If you answer 'no' to any questions you can always re-run
      the script again later
DONE

if( $action eq 'install' ) {
    install();
}

if( $action eq 'uninstall' ) {
    uninstall();
}

if( $action eq 'upgrade' ) {

    print <<DONE;
I would like to uninstall TWikiDrawPlugin before upgrading, to
make sure that any files that have been removed from the
package are also removed from your installation.
DONE
    my $reply = ask("Is it OK to uninstall the existing package?");
    if( $reply ) {
        uninstall();
    } else {
        print <<DONE;
Installation will overwrite any files previously installed for
TWikiDrawPlugin.
DONE
        $reply = ask('Is this OK?');
        exit unless $reply;
    }

    installPackage( "$PACKAGES_URL/TWikiDrawPlugin/", 'TWikiDrawPlugin' );
}
