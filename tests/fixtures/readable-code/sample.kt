// expect: vague-name:q vague-name:tmp no-docstring:sumAll

fun sumAll(values: List<Int>): Int {
    val q = 1
    var tmp = q
    for (amount in values) {
        tmp += amount
    }
    return tmp
}

/** 이름을 다듬는다. "val x = 1" 은 글이다. */
fun tidyName(rawName: String): String {
    val trimmed = rawName.trim()
    val lowered = trimmed.lowercase()
    val note = """val y = { }"""
    println(note)
    return lowered
}
