package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C21SwitchExpression {
    @GetMapping("/c21")
    public int h(int k, boolean a, boolean b) {
        return switch (k) {                    // +1
            case 1 -> a ? 1 : 2;               // +2
            case 2 -> {
                if (b) yield 3;                // +2
                yield 4;
            }
            default -> 0;
        };
    }
}
