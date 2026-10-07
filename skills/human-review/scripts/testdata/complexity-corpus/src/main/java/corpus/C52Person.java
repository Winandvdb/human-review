package corpus;

import lombok.Data;

@Data
public class C52Person {
    private String name;

    public String greeting() {
        return name == null ? "hi" : "hi " + name;   // +1
    }

    public void setNickname(String n) {
        if (n == null) return;                       // a hand-written setter of the same shape, not reached
    }
}
