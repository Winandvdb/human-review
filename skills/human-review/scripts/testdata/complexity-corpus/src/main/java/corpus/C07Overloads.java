package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C07Overloads {
    private final C07Fmt fmt = new C07Fmt();

    @GetMapping("/c07")
    public String h() {
        return fmt.render(5);
    }
}
