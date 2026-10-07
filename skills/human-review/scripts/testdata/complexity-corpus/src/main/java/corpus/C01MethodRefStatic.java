package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C01MethodRefStatic {
    @GetMapping("/c01")
    public List<Integer> h(List<Integer> xs) {
        return xs.stream().map(C01Util::twice).toList();
    }
}
