#!/usr/bin/perl

=head1 NAME

update_tmserver.pl - Populate Elasticsearch index with new translations

=head1 DESCRIPTION

B<update_tmserver.pl> checks if there are any new translations in the Pootle database,
and feeds them into 'translations' index of the locally installed Elasticsearch database.

=head1 SYNOPSIS

update_tmserver.pl [--overwrite] [--rebuild] [--dry-run]

=head1 OPTIONS

=over 8

=item B<--overwrite>

Process all items, not just the new ones (useful to overwrite properties
while keeping the index in a working condition)

=item B<--rebuild>

Drop the entire index on start and update everything from scratch

=item B<--dry-run>

Just report the number of translations to index and quit

=back

=cut

use strict;

use Data::Dumper;
use DBI;
use Digest::MD5 qw(md5_hex);
use Elasticsearch;
use Elasticsearch::Bulk;
use Getopt::Long;
use Pod::Usage;

# Hardcoded see config INDEX_NAME
my $INDEX_NAME = 'translations';
my $BULK_CHUNK_SIZE = 5000;

my $MYSQL_PARAMS = {
    'mysql_enable_utf8' => 1,
    'mysql_bind_type_guessing' => 1
};

my $MYSQL_USER = 'pootle';
my $MYSQL_PASS = $ENV{'L10N_POOTLE_MYSQL_PASSWORD'} or die "L10N_POOTLE_MYSQL_PASSWORD environment variable not set";

my $t1 = time;

$| = 1; # autoflush output
binmode(STDOUT, ':utf8'); # to avoid 'Wide character in print' warning

my ($help, $overwrite, $rebuild, $dry_run);

my $result = GetOptions(
    "help" => \$help,
    "overwrite" => \$overwrite,
    "rebuild" => \$rebuild,
    "dry-run"      => \$dry_run,
);

pod2usage(-verbose => 2, -exitstatus => 0, -noperldoc => 1) if $help;

my $db = DBI->connect("DBI:mysql:pootle", $MYSQL_USER, $MYSQL_PASS, $MYSQL_PARAMS) or die "Can't connect to the database: $!";
my $es = Elasticsearch->new();
my $bulk = Elasticsearch::Bulk->new(
    es        => $es,
    index     => $INDEX_NAME,
    max_count => $BULK_CHUNK_SIZE,
);

my $last_indexed_revision = -1;

if ($rebuild && !$dry_run) {
    eval {
        $es->indices->delete(index => $INDEX_NAME);
    };
}

if (!$rebuild && !$overwrite) {
    my $result = $es->search(
        index => $INDEX_NAME,
        body => {
            query => {
                match_all => {}
            },
            facets => {
                stat1 => {
                    statistical => {
                        field => 'revision'
                    }
                }
            }
        }
    );

    $last_indexed_revision = $result->{facets}->{stat1}->{max};
}

print "Last indexed revision = ", $last_indexed_revision, "\n";

my $sqlquery =
    "SELECT COUNT(*) ".
    "FROM pootle_store_unit ".
    "WHERE target_f IS NOT NULL AND target_f != '' ".
    "AND revision > $last_indexed_revision";

my $sth = $db->prepare($sqlquery);
$sth->execute || die $sth->errstr;

my $total;
if (my $ar = $sth->fetchrow_arrayref()) {
    $total = $ar->[0];
}

if (!$total) {
    print "No translations to index\n";
    exit;
} else {
    print "$total translations to index\n";
}

exit if $dry_run;

$sqlquery =
    "SELECT u.id, u.revision, u.source_f AS source, u.target_f AS target, ".
        "pu.username, pu.full_name, pu.email, ".
        "p.fullname AS project, s.pootle_path AS path, ".
        "l.code AS language ".
    "FROM pootle_store_unit u ".
    "LEFT OUTER JOIN pootle_user pu ON u.submitted_by_id = pu.id ". # record might not be present
    "JOIN pootle_store_store s on s.id = u.store_id ".
    "JOIN pootle_app_translationproject tp on tp.id = s.translation_project_id ".
    "JOIN pootle_app_language l on l.id = tp.language_id ".
    "JOIN pootle_app_project p on p.id = tp.project_id ".
    "WHERE u.target_f IS NOT NULL AND u.target_f != '' ".
    "AND revision > $last_indexed_revision";

$sth = $db->prepare($sqlquery);
$sth->execute || die $sth->errstr;

my $i = 0;
my $hr;
while ($hr = $sth->fetchrow_hashref()) {
    $i++;

    my $fullname = $hr->{full_name} || $hr->{username};
    my $email_md5 = md5_hex($hr->{email}) if $hr->{email} ne '';

    $bulk->index({
        type   => $hr->{language},
        id     => $hr->{id},
        source => {
            revision  => $hr->{revision} + 0, # this must be an integer for statistical queries to work
            project   => $hr->{project},
            path      => $hr->{path},
            username  => $hr->{username},
            fullname  => $fullname,
            email_md5 => $email_md5,
            source    => $hr->{source},
            target    => $hr->{target}
        }
    });

    if (($i % 1000 == 0) || ($i == $total)) {
        my $percent = sprintf("%.1f", 100 * $i / $total);
        print "\r$i ($percent%)";
    }
}

$bulk->flush;

print "\n";

if ($i != $total) {
    print "Oops. Stopped at i = $i\n";
}

my $t2 = time;
my $dt = $t2 - $t1;
my $m = int($dt / 60);
my $s = $dt % 60;

if ($m) {
    print "\nExecution time: $m min $s sec\n";
} else {
    print "\nExecution time: $s sec\n";
}
