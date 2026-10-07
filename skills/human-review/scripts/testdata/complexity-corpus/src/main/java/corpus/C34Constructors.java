package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C34Constructors {
    @GetMapping("/c34")
    public Object h(String cfg) {
        return new C34Service(cfg);
    }
}
