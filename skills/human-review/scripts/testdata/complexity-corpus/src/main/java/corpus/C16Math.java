package corpus;

public final class C16Math {
    public static int clamp(int x, int lo, int hi) {
        if (x < lo) {                          // +1
            return lo;
        } else if (x > hi) {                   // +1
            return hi;
        } else {                               // +1
            return x;
        }
    }
}
