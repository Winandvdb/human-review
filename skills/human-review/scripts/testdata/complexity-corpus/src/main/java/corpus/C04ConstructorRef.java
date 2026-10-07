package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C04ConstructorRef {
    @GetMapping("/c04")
    public List<C04Box> h(List<String> names) {
        return names.stream().map(C04Box::new).toList();
    }
}
