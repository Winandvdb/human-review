package corpus;

public class C34Service {
    private final String cfg;

    public C34Service(String cfg) {
        if (cfg == null) throw new IllegalArgumentException();   // +1
        this.cfg = cfg;
    }

    public C34Service(int retries) {
        String c = "";
        for (int i = 0; i < retries; i++) c += i;               // +1, not reached
        this.cfg = c;
    }
}
