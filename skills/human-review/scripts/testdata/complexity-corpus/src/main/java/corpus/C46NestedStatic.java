package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C46NestedStatic {
    @GetMapping("/c46")
    public int h(int x) {
        return C46Outer.Inner.util(x);
    }
}
