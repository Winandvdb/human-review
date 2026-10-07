package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C19BracelessNesting {
    @GetMapping("/c19")
    public int h(int a, int b) {
        if (a > 0)                             // +1
            if (b > 0)                         // +2
                return 1;
        for (int i = 0; i < a; i++)            // +1
            if (i == b) return i;              // +2
        return 0;
    }
}
