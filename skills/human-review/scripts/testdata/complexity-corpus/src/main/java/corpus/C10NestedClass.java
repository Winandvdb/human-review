package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C10NestedClass {
    @GetMapping("/c10")
    public int h() {
        return new Inner().work(3);
    }

    /** Same name as Inner.work, never called: a nested class is not its outer class. */
    int work(int n) {
        for (int i = 0; i < n; i++) {          // +1, not reached
            n--;
        }
        return n;
    }

    static class Inner {
        int work(int n) {
            if (n > 2) return 2;               // +1
            return n;
        }
    }
}
