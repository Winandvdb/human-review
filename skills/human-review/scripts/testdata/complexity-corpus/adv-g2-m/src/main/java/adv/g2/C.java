// From the adversarial review of 7 Oct 2026 (case g2_lombok_ctor).
package adv.g2;
import org.springframework.web.bind.annotation.*;
@RestController
public class C { @GetMapping("/g2") public Object a() { return new Req(); } }
