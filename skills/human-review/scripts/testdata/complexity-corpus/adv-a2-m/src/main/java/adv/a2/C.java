// From the adversarial review of 7 Oct 2026 (case a2_var_repo).
package adv.a2;
import org.springframework.web.bind.annotation.*;
@RestController
public class C {
  private final OwnerRepository repo;
  C(OwnerRepository repo) { this.repo = repo; }
  @GetMapping("/a2") public int a(int id) { var o = repo.findById(id).orElseThrow(); return o.total(); }
  @GetMapping("/a3") public int b(int id) { return repo.findById(id).orElseThrow().total(); }
  @GetMapping("/a4") public int c(int id) { Owner o = repo.findById(id).orElseThrow(); return o.total(); }
  @GetMapping("/a5") public java.util.List<Integer> d() { return repo.findAll().stream().map(Owner::total).toList(); }
  @GetMapping("/a6") public java.util.List<Integer> e() { return repo.findAll().stream().map(o -> o.total()).toList(); }
}
