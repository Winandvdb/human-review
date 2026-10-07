package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C20BracelessElseIf {
    @GetMapping("/c20")
    public int h(boolean a, boolean b) {
        int x;
        if (a) x = 1;                          // +1
        else if (b) x = 2;                     // +1
        else x = 3;                            // +1
        return x;
    }
}
