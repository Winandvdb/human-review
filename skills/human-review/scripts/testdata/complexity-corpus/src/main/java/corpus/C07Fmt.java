package corpus;

public class C07Fmt {
    public String render(int n) {
        if (n < 0) return "-";                 // +1
        return String.valueOf(n);
    }

    public String render(String s) {
        for (char c : s.toCharArray()) {       // +1, never reached from /c07
            if (c == ' ') return "_";          // +2
        }
        return s;
    }
}
