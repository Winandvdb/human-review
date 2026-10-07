package corpus;

public class C17Base {
    protected int n;

    public void save() {
        for (int i = 0; i < n; i++) {          // +1
            System.out.println(i);
        }
    }
}
