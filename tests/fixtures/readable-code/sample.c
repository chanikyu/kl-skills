// expect: vague-name:q vague-name:tmp no-docstring:sum_all

#include <stdio.h>

int sum_all(const int *values, int count)
{
    int q = 0;
    int tmp = q;
    for (int index = 0; index < count; index++) {
        tmp += values[index];
    }
    return tmp;
}

/* 괄호 문자를 센다. '{' 와 "{" 는 세지 않는다. */
static int count_braces(const char *text)
{
    int brace_count = 0;
    char open_brace = '{';
    const char *label = "int x = 1;";
    for (; *text; text++) {
        if (*text == open_brace) brace_count++;
    }
    (void)label;
    return brace_count;
}
