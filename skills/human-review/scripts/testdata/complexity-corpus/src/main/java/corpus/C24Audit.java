package corpus;

/** Declares `save`: the repository's inherited save must not be mistaken for it. */
public class C24Audit {
    public void save(Object o) {
        if (o == null) return;                 // +1, never reached from /c24
        System.out.println(o);
    }
}
