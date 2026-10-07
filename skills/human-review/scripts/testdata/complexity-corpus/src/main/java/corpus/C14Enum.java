package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C14Enum {
    @GetMapping("/c14")
    public int h(C14Op op) {
        return op.apply(1, 2);
    }
}
