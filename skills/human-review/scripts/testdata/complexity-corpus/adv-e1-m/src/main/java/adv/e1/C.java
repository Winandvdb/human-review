// From the adversarial review of 7 Oct 2026 (case e1_lombok_chain).
package adv.e1;
import org.springframework.web.bind.annotation.*;
@RestController
public class C {
  @GetMapping("/e1") public Long a(Training t) { return t.getTeacher().getId(); }
}
