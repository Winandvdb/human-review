package corpus;

public enum C14Op {
    PLUS {
        int apply(int a, int b) {
            return a + b;
        }
    },
    MINUS {
        int apply(int a, int b) {
            if (a < b) return 0;               // +1
            return a - b;
        }
    };

    abstract int apply(int a, int b);

    int unused() {
        while (true) {                         // +1, not reached
            return 0;
        }
    }
}
