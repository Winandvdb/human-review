// From the second adversarial review of 7 Oct 2026 (case p4_twin_static).
package adv2.p4.y;
import org.springframework.web.bind.annotation.*;
import static adv2.p4.x.Util.*;
@RestController
public class CB { @GetMapping("/t1") public int b() { return f(1); } }
