package corpus;

public final class C30Log {
    public static String log(String fmt, Object... args) {
        if (args.length == 0) return fmt;      // +1
        return String.format(fmt, args);
    }

    public static String log(String msg) {
        for (int i = 0; i < 2; i++) msg += "!";    // +1, not reached
        return msg;
    }
}
