package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C06Chained {
    @GetMapping("/c06")
    public int h() {
        return C06Factory.create().normalize().score();
    }
}
