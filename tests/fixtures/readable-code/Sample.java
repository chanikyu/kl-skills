// expect: vague-name:q vague-name:tmp no-docstring:sumAll

/** 시험용 예제. */
public class Sample {
    static int sumAll(int[] values) {
        int q = 1;
        int tmp = q;
        for (int amount : values) {
            tmp += amount;
        }
        return tmp;
    }

    /** 이름을 다듬는다. "int x = 1;" 은 글이다. */
    public String tidyName(String rawName) {
        String trimmed = rawName.trim();
        String lowered = trimmed.toLowerCase();
        char brace = '{';
        System.out.println(brace);
        return lowered;
    }
}
