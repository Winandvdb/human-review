package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C51SwitchPatternGuard {
    @GetMapping("/c51")
    public String h(Object o, boolean strict) {
        return switch (o) {                                   // +1
            case String s when s.isEmpty() && strict -> "e";  // +1 (&&)
            case String s -> s;
            case Integer i -> i > 0 ? "pos" : "neg";          // +2
            default -> "?";
        };
    }
}
