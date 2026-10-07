package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C25BooleanSequences {
    @GetMapping("/c25")
    public boolean h(boolean a, boolean b, boolean c, boolean d) {
        if (a && b && c || d) {                // +1 if, +1 &&, +1 ||
            return true;
        }
        boolean x = a && !(b || c) && d;       // +1 for the && run, +1 for the || inside the !
        return x;
    }
}
