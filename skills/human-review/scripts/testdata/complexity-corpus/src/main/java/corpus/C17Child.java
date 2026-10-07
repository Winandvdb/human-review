package corpus;

public class C17Child extends C17Base {
    public C17Child() {
        this(5);
    }

    public C17Child(int n) {
        if (n < 0) throw new IllegalArgumentException();   // +1
        this.n = n;
    }

    @Override
    public void save() {
        if (n == 0) return;                    // +1
        super.save();
    }
}
