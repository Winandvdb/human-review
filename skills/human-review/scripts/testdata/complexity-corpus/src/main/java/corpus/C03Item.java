package corpus;

public class C03Item {
    private String name;

    public String label() {
        return name == null ? "?" : name;     // +1
    }
}
