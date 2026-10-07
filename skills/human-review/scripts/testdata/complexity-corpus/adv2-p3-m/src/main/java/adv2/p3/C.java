// From the second adversarial review of 7 Oct 2026 (case p3_ids).
package adv2.p3;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;
@RestController
public class C {
  private final OwnerRepository repo;
  C(OwnerRepository repo) { this.repo = repo; }
  // expected Owner.isValid = 1 only
  @GetMapping("/i1") public boolean a(OwnerId id) { return repo.findById(id).orElseThrow().isValid(); }
  // expected Owner.isValid = 1 only
  @GetMapping("/i2") public boolean b(OwnerId id) { return repo.getReferenceById(id).isValid(); }
  // count() returns long: nothing project. expected 0
  @GetMapping("/i3") public boolean c() { return repo.findAll().stream().allMatch(o -> o.isValid()); }
}
