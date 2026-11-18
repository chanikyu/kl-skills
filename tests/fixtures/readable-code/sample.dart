// expect: vague-name:q vague-name:tmp no-docstring:sumAll

int sumAll(List<int> values) {
  var q = 1;
  int tmp = q;
  for (final amount in values) {
    tmp += amount;
  }
  return tmp;
}

/// 이름을 다듬는다. 'var x = 1' 은 글이다.
String tidyName(String rawName) {
  final trimmed = rawName.trim();
  final lowered = trimmed.toLowerCase();
  const note = '{ var y = 2 }';
  print(note);
  return lowered;
}
