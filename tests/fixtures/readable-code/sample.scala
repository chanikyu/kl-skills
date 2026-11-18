// expect: vague-name:q vague-name:tmp no-docstring:sumAll

/** 시험용 예제. */
object Sample {
  def sumAll(values: Seq[Int]): Int = {
    val q = 1
    var tmp = q
    for (amount <- values) {
      tmp += amount
    }
    tmp
  }

  /** 이름을 다듬는다. "val x = 1" 은 글이다. */
  def tidyName(rawName: String): String = {
    val trimmed = rawName.trim
    val lowered = trimmed.toLowerCase
    val note = "{ val y = 2 }"
    println(note)
    lowered
  }
}
