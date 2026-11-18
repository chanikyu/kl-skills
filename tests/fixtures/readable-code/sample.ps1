# expect: vague-name:q vague-name:tmp no-docstring:Get-Total

function Get-Total {
    param($Values)
    $q = 1
    $tmp = $q
    foreach ($amount in $Values) {
        $tmp += $amount
    }
    return $tmp
}

<# 이름을 다듬는다. $x = 1 은 주석이다. #>
function Format-Name {
    param($RawName)
    $trimmed = $RawName.Trim()
    $lowered = $trimmed.ToLower()
    $note = "{ `$y = 2 }"
    Write-Output $note
    return $lowered
}
