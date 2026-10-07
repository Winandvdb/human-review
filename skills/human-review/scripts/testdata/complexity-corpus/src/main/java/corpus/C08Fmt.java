package corpus;

public class C08Fmt {
    public String show(Object o) {
        if (o == null) return "null";          // +1, not reached
        return o.toString();
    }

    public String show(String s) {
        if (s.isEmpty()) {                     // +1
            return "empty";
        } else {                               // +1
            return s;
        }
    }
}
