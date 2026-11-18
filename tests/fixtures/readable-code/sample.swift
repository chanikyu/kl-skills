// expect: vague-name:q vague-name:tmp no-docstring:sumAll

import Foundation

func sumAll(_ values: [Int]) -> Int {
    let q = 1
    var tmp = q
    for amount in values {
        tmp += amount
    }
    return tmp
}

/// 문장 길이를 센다. "let x = 1" 같은 글은 이름이 아니다.
func sentenceLength(_ sentence: String) -> Int {
    let note = "var y = { }"
    let trimmed = sentence.trimmingCharacters(in: .whitespaces)
    let wordCount = trimmed.split(separator: " ").count
    print(note)
    return wordCount
}
