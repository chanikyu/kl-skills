<?php
// expect: vague-name:q vague-name:tmp no-docstring:sumAll

function sumAll(array $values): int
{
    $q = 1;
    $tmp = $q;
    foreach ($values as $amount) {
        $tmp += $amount;
    }
    return $tmp;
}

/** 이름을 다듬는다. '$x = 1' 은 글이다. */
function tidyName(string $rawName): string
{
    $trimmed = trim($rawName);
    $lowered = strtolower($trimmed);
    $note = "{ \$y = 2 }";
    echo $note;
    return $lowered;
}
