package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C05Lambda {
    @GetMapping("/c05")
    public void h(List<Integer> xs) {
        xs.forEach(x -> {
            if (x > 0) {                       // +2 (inside a lambda: nesting 1)
                System.out.println(x);
            }
        });
    }
}
