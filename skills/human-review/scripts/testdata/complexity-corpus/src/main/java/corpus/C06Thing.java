package corpus;

public class C06Thing {
    int n;

    public C06Thing normalize() {
        if (n < 0) n = 0;                      // +1
        return this;
    }

    public int score() {
        int s = 0;
        while (s < n) s++;                     // +1
        return s;
    }
}
