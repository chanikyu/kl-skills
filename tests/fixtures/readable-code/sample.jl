# expect: vague-name:q vague-name:tmp

function sum_all(values)
    q = 1
    tmp = q
    for amount in values
        tmp += amount
    end
    return tmp
end
#= x = 1 은 주석이다 =#
note = "y = 2"
