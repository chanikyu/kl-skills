// expect: vague-name:q vague-name:tmp no-docstring:sum_all

fn sum_all(values: &[i32]) -> i32 {
    let q = 1;
    let mut tmp = q;
    for amount in values {
        tmp += amount;
    }
    tmp
}

/// 괄호 개수의 차이. 문자 '{' 는 세지 않는다.
fn bracket_distance<'a>(text: &'a str) -> usize {
    let open_count = text.matches('{').count();
    let close_count = text.matches('}').count();
    if let Some(first_char) = text.chars().next() {
        let _ = first_char;
    }
    open_count.abs_diff(close_count)
}
