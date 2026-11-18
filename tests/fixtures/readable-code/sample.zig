// expect: vague-name:q vague-name:tmp no-docstring:sumAll

const std = @import("std");

fn sumAll(values: []const i32) i32 {
    const q: i32 = 1;
    var tmp: i32 = q;
    for (values) |amount| {
        tmp += amount;
    }
    return tmp;
}

/// 괄호를 센다. '{' 는 세지 않는다.
fn countBraces(text: []const u8) usize {
    var brace_count: usize = 0;
    for (text) |letter| {
        if (letter == '{') brace_count += 1;
    }
    const label = "const x = 1;";
    _ = label;
    return brace_count;
}
