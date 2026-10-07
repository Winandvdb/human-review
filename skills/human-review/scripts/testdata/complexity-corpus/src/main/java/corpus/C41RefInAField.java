package corpus;

import java.util.function.Function;
import org.springframework.web.bind.annotation.*;

@RestController
public class C41RefInAField {
    @GetMapping("/c41")
    public int h(int n) {
        Function<Integer, Integer> f = C41RefInAField::inc;
        return f.apply(n);
    }

    static Integer inc(Integer x) {
        if (x == null) return 0;               // +1
        return x + 1;
    }
}
