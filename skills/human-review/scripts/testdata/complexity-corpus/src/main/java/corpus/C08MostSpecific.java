package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C08MostSpecific {
    private final C08Fmt fmt = new C08Fmt();

    @GetMapping("/c08")
    public String h() {
        return fmt.show("x");                  // show(String) is more specific than show(Object)
    }
}
