package corpus;

public final class C35Conv {
    public static String conv(Integer i) {
        if (i == null) return "";              // +1
        return i.toString();
    }

    public static String conv(String s) {
        for (int k = 0; k < 2; k++) s += k;    // +1, not reached: the stream carries Integers
        return s;
    }
}
