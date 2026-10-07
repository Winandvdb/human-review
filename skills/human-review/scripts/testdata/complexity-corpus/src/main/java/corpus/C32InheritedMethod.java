package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C32InheritedMethod {
    @GetMapping("/c32")
    public int h() {
        C32Child c = new C32Child();
        return c.compute();
    }
}
