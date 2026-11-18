// expect: vague-name:q vague-name:tmp no-docstring:sumAll

def sumAll(List values) {
    def q = 1
    def tmp = q
    values.each { amount ->
        tmp += amount
    }
    return tmp
}

/** 이름을 다듬는다. "def x = 1" 은 글이다. */
String tidyName(String rawName) {
    def trimmed = rawName.trim()
    def lowered = trimmed.toLowerCase()
    def note = '{ def y = 2 }'
    println note
    return lowered
}
