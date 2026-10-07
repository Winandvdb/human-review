package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C35OverloadedRef {
    @GetMapping("/c35")
    public List<String> h(List<Integer> xs) {
        return xs.stream().map(C35Conv::conv).toList();
    }
}
