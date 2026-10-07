package corpus;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class C27GenericMethod {
    @GetMapping("/c27")
    public Integer h(List<Integer> xs) {
        return C27Util.max(xs);
    }
}
