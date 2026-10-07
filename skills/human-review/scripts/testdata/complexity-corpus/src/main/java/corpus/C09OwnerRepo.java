package corpus;

public class C09OwnerRepo implements C09Repo<C09Owner> {
    @Override
    public C09Owner load(String id) {
        if (id == null) throw new IllegalArgumentException();   // +1
        return new C09Owner();
    }
}
