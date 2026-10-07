// From the adversarial review of 7 Oct 2026 (case a3_slf4j).
package adv.a3;
import org.springframework.web.bind.annotation.*;
import lombok.extern.slf4j.Slf4j;
@Slf4j
@RestController
public class C {
  @GetMapping("/s") public void a() { log.error("x"); log.info("y"); }
}
