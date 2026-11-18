# expect: vague-name:q vague-name:tmp

def sum_all(values)
  q = 1
  tmp = q
  values.each { |amount| tmp += amount }
  tmp
end

# 이름을 다듬는다. "x = 1" 은 글이다.
def tidy_name(raw_name)
  trimmed = raw_name.strip
  note = "y = 2"
  trimmed.downcase
end
