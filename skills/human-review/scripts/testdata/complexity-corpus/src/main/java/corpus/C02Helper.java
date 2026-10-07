package corpus;

public class C02Helper {
    public boolean check(String s) {
        for (char c : s.toCharArray()) {      // +1
            if (c == 'x') {                    // +2
                return true;
            }
        }
        return false;
    }
}
