package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C50IndirectRecursion {
    @GetMapping("/c50")
    public boolean h(int n) {
        return isEven(n);
    }

    boolean isEven(int n) {
        if (n == 0) return true;               // +1
        return isOdd(n - 1);
    }

    boolean isOdd(int n) {
        if (n == 0) return false;              // +1
        return isEven(n - 1);
    }
}
