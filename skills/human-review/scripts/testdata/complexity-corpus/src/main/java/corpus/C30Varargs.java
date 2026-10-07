package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C30Varargs {
    @GetMapping("/c30")
    public String h() {
        return C30Log.log("a %s", 1);
    }
}
