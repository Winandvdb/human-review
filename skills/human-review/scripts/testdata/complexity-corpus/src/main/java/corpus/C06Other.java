package corpus;

/** Declares `normalize` too: a name-only guess cannot tell it from C06Thing's. */
public class C06Other {
    public String normalize(String s) {
        if (s == null) return "";              // +1, never reached from /c06
        return s.trim();
    }
}
