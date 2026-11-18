# expect: vague-name:q vague-name:tmp no-docstring:sum_all

use strict;

sub sum_all {
    my ($first_value) = @_;
    my $q = 1;
    my $tmp = $q;
    $tmp += $first_value;
    return $tmp;
}

# 이름을 다듬는다. '$x = 1' 은 글이다.
sub tidy_name {
    my $raw_name = shift;
    my $trimmed = $raw_name;
    $trimmed =~ s/^\s+//;
    my $note = "{ my \$y = 2 }";
    return lc $trimmed;
}
