package corpus;

/** A second `clamp`: a guess by name alone has two to choose from. */
public class C16Other {
    public double clamp(double v) {
        for (int i = 0; i < 3; i++) v /= 2;    // +1, not reached
        return v;
    }
}
