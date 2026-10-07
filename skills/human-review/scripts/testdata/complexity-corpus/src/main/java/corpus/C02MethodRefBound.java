package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C02MethodRefBound {
    private final C02Helper helper = new C02Helper();

    @GetMapping("/c02")
    public List<Boolean> h(List<String> xs) {
        return xs.stream().map(helper::check).toList();
    }
}
