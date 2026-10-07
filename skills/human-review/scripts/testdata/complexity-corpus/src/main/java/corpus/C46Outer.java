package corpus;

public class C46Outer {
    static int util(int x) {
        while (x > 100) x /= 2;                // +1, not reached: Inner.util is a different method
        return x;
    }

    public static class Inner {
        public static int util(int x) {
            return x < 0 ? -x : x;             // +1
        }
    }
}
