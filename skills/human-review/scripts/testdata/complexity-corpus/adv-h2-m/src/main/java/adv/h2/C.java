// From the adversarial review of 7 Oct 2026 (case h2_fqann).
package adv.h2;
@org.springframework.web.bind.annotation.RestController
public class C {
  @org.springframework.web.bind.annotation.GetMapping("/fq") public int a(int n) { if (n > 0) { return 1; } return 0; }
  @org.springframework.scheduling.annotation.Scheduled(fixedRate = 1000) public void job() { }
}
