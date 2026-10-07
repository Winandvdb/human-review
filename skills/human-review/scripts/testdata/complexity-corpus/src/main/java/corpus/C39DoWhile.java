package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C39DoWhile {
    @GetMapping("/c39")
    public int h(int x) {
        do {                                   // +1
            x--;
        } while (x > 0);
        return x;
    }
}
