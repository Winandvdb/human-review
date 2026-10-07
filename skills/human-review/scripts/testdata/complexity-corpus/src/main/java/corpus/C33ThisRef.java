package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C33ThisRef {
    @GetMapping("/c33")
    public void h(List<String> items) {
        items.forEach(this::handle);
    }

    void handle(String s) {
        if (s.isBlank()) return;               // +1
        System.out.println(s);
    }
}
