package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C17SuperCall {
    private final C17Child child = new C17Child(1);

    @GetMapping("/c17")
    public void h() {
        child.save();
    }
}
