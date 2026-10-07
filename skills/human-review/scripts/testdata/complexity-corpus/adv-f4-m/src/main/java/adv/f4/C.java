// From the adversarial review of 7 Oct 2026 (case f4_library_chain).
package adv.f4;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
@RestController
public class C {
  private final RestTemplate rt = new RestTemplate();
  @GetMapping("/f4") public int a() { return rt.getForObject("u", Owner.class).score(); }
  @GetMapping("/f5") public int b(ResponseEntity<Owner> r) { return r.getBody().score(); }
}
