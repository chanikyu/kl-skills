// expect: vague-name:q vague-name:tmp no-docstring:SumAll

package sample

func SumAll(values []int) int {
	q := 1
	var tmp = q
	for _, amount := range values {
		tmp += amount
	}
	return tmp
}

// Distance 는 두 수의 차이다. "x := 1" 은 글이다.
func (counter *Counter) Distance(left int, right int) int {
	gap := left - right
	if gap < 0 {
		gap = -gap
	}
	label := `raw { string`
	_ = label
	return gap
}

// Counter 는 수를 센다.
type Counter struct {
	total int
}
