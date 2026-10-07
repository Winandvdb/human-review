package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C17bThisCtor {
    @GetMapping("/c17b")
    public Object h() {
        return new C17Child();                 // C17Child() -> this(5) -> C17Child(int)
    }
}
