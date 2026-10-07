package corpus;

import java.util.List;

public final class C27Util {
    public static <T extends Comparable<T>> T max(List<T> xs) {
        T best = null;
        for (T x : xs)                                       // +1
            if (best == null || x.compareTo(best) > 0)       // +2, +1 for ||
                best = x;
        return best;
    }
}
