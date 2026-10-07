package corpus;

public class C09Owner {
    int kind;

    public String describe() {
        switch (kind) {                        // +1
            case 1: return "one";
            default: return "many";
        }
    }
}
