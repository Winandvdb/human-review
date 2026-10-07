// From the second adversarial review of 7 Oct 2026 (case p1_payload).
package adv2.p1;
import org.springframework.web.bind.annotation.*;
import org.springframework.data.domain.*;
import org.springframework.http.ResponseEntity;
import reactor.core.publisher.Mono;
import java.util.*;
@RestController
public class C {
  private final PostRepository repo;
  C(PostRepository repo) { this.repo = repo; }
  // Page.getContent() is the library's; Post.getContent (1) must NOT be followed. expected 0
  @GetMapping("/p1") public Object a(Pageable p) { return repo.findAll(p).getContent(); }
  // List.isEmpty(); Post.isEmpty (3) must NOT be followed. expected 0
  @GetMapping("/p2") public boolean b() { return repo.findAll().isEmpty(); }
  // Map<Post,Vet>.get(k) is a Vet: only Vet.check (3). expected 3
  @GetMapping("/p3") public int c(ResponseEntity<Map<Post, Vet>> r, Post k) { return r.getBody().get(k).check(); }
  // zipWith: v is a Vet; expected Vet.check 3
  @GetMapping("/p4") public Mono<Integer> d(Mono<Post> mp, Mono<Vet> mv) { return mp.zipWith(mv, (p, v) -> v.check()); }
  // Mono.just(post).map(x -> x.check()) -> Post.check 1
  @GetMapping("/p5") public Mono<Integer> e(Post post) { return Mono.just(post).map(x -> x.check()); }
  // Optional.get() vs ... findById(id).get().check() -> Post.check 1
  @GetMapping("/p6") public int f(long id) { return repo.findById(id).get().check(); }
}
