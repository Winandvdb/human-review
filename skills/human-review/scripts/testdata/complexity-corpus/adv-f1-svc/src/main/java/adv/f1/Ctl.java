// From the adversarial review of 7 Oct 2026 (case f1_openapi_default).
package adv.f1;
import org.springframework.web.bind.annotation.*;
@RestController
public class Ctl implements Api {
  @Override public String f1(int n) { for (int i = 0; i < n; i++) { if (i > 2) { return "real"; } } return ""; }
}
