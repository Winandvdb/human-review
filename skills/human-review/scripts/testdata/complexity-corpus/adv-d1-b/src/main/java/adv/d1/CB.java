// From the adversarial review of 7 Oct 2026 (case d1_dupfqcn).
package adv.d1;
import org.springframework.web.bind.annotation.*;
@RestController
public class CB { @GetMapping("/db") public int b() { return Util.f(1); } }
