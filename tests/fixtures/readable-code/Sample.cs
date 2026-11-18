// expect: vague-name:q vague-name:tmp no-docstring:SumAll

/// <summary>시험용 예제.</summary>
public class Sample
{
    public static int SumAll(int[] values)
    {
        var q = 1;
        int tmp = q;
        foreach (var amount in values)
        {
            tmp += amount;
        }
        return tmp;
    }

    /// <summary>이름을 다듬는다.</summary>
    [Obsolete]
    public string TidyName(string rawName)
    {
        string trimmed = rawName.Trim();
        string lowered = trimmed.ToLower();
        char brace = '{';
        Console.WriteLine(brace);
        return lowered;
    }
}
