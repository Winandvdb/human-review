package corpus;

public record C13Range(int lo, int hi) {
    public C13Range {
        if (lo > hi) throw new IllegalArgumentException();   // +1
    }

    public boolean contains(int x) {
        return x >= lo && x <= hi;             // +1
    }

    public int width() {
        return hi > lo ? hi - lo : 0;          // +1, not reached
    }
}
