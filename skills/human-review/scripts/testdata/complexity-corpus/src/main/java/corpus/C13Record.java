package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C13Record {
    @GetMapping("/c13")
    public boolean h() {
        C13Range r = new C13Range(1, 5);
        return r.contains(r.lo());              // lo() is the implicit accessor: nothing to run
    }
}
