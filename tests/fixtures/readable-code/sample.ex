# expect: vague-name:q vague-name:tmp

defmodule Sample do
  def sum_all(values) do
    q = 1
    tmp = q
    Enum.reduce(values, tmp, fn amount, total -> total + amount end)
  end

  # "x = 1" 은 글이다
  def tidy_name(raw_name) do
    trimmed = String.trim(raw_name)
    String.downcase(trimmed)
  end
end
