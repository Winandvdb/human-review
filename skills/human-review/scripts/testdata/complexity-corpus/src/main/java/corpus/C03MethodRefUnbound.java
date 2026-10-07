package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C03MethodRefUnbound {
    @GetMapping("/c03")
    public List<String> h(List<C03Item> items) {
        return items.stream().map(C03Item::label).toList();
    }
}
