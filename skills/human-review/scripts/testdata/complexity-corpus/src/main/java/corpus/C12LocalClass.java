package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C12LocalClass {
    @GetMapping("/c12")
    public int h() {
        class Local {
            int f(int x) {
                return x > 0 ? 1 : 0;          // +2: nested in a local class
            }
        }
        return new Local().f(3);
    }
}
