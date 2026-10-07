package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C15InterfaceMethods {
    @GetMapping("/c15")
    public String h() {
        return C15Shape.unit().describe();
    }
}
