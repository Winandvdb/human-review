package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C49PatternMatching {
    @GetMapping("/c49")
    public int h(Object o) {
        if (o instanceof String s && !s.isEmpty()) {   // +1 if, +1 &&
            return s.length();
        }
        return 0;
    }
}
