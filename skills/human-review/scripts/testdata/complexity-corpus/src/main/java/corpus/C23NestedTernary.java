package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C23NestedTernary {
    @GetMapping("/c23")
    public int h(boolean a, boolean b) {
        return a ? (b ? 1 : 2) : 3;            // +1, and +2 for the nested one
    }
}
