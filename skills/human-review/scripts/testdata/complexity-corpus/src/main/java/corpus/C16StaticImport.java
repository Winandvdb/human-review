package corpus;

import static corpus.C16Math.clamp;

import org.springframework.web.bind.annotation.*;

@RestController
public class C16StaticImport {
    @GetMapping("/c16")
    public int h(int x) {
        return clamp(x, 0, 10);
    }
}
