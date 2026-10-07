// From the adversarial review of 7 Oct 2026 (case a1_inherited_impl).
package adv.a1;
import org.springframework.web.bind.annotation.*;
@RestController
public class C {
  private final Svc svc;
  C(Svc svc) { this.svc = svc; }
  @GetMapping("/a1") public int a(int z) { return svc.doIt(z); }
}
