// From the adversarial review of 7 Oct 2026 (case f1_openapi_default).
package adv.f1;
import org.springframework.web.bind.annotation.*;
public interface Api {
  @GetMapping("/f1") default String f1(int n) { if (n > 0) { return "stub"; } return null; }
}
