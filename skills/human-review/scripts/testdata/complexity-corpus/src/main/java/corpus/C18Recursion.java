package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C18Recursion {
    @GetMapping("/c18")
    public int h(String s) {
        return fact(s);
    }

    int fact(String s) {
        return fact(Integer.parseInt(s));      // the other overload: not recursion
    }

    int fact(int n) {
        if (n <= 1) return 1;                  // +1
        return n * fact(n - 1);                // +1 recursion
    }
}
