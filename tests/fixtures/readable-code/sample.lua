-- expect: vague-name:q vague-name:tmp

local function sum_all(values)
  local q = 1
  local tmp = q
  for _, amount in ipairs(values) do
    tmp = tmp + amount
  end
  return tmp
end
--[[ local x = 1 은 주석이다 ]]
local note = "local y = 2"
