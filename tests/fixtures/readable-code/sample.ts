// expect: vague-name:q vague-name:tmp no-docstring:sumAll

const q = 1;
let tmp = q + 1;

function sumAll(values: number[]): number {
  let total = 0;
  for (const amount of values) {
    total += amount;
  }
  total += q;
  return total + tmp;
}

/** 두 수를 더한다. 합계 칸이 쓴다. */
export const addPair = (left: number, right: number): number => {
  const pairTotal = left + right;
  const label = "let y = { not code }";
  // const z = 1 은 주석이라 이름이 아니다
  console.log(label);
  return pairTotal;
};

/** 수를 센다. */
class Counter {
  /** 하나 늘리고 새 값을 준다. */
  increment(step: number): number {
    const nextValue = step + 1;
    const doubled = nextValue * 2;
    const tripled = nextValue * 3;
    return doubled + tripled;
  }
}
