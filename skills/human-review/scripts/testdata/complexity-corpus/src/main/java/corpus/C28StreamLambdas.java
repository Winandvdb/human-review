package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C28StreamLambdas {
    @GetMapping("/c28")
    public List<String> h(List<Integer> xs) {
        return xs.stream()
                .filter(x -> x > 0 && x < 10)               // +1 (&&; boolean runs ignore nesting)
                .map(x -> x > 5 ? "hi" : "lo")              // +2 (a ternary inside a lambda)
                .toList();
    }
}
