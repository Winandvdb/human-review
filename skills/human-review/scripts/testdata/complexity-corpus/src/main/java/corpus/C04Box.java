package corpus;

public class C04Box {
    private final String value;

    public C04Box(String value) {
        if (value.isEmpty()) {                 // +1
            throw new IllegalArgumentException();
        }
        this.value = value;
    }
}
