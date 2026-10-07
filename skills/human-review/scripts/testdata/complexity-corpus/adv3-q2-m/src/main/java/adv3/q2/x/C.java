// From the third adversarial review of 7 Oct 2026 (case q2_spec).
package adv3.q2.x;
import org.springframework.web.bind.annotation.*;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.jdbc.core.RowMapper;
@RestController
public class C {
  // root is Root<Owner>, not Owner: expected 0, nothing followed, ideally nothing reported
  @GetMapping("/s1") public Specification<Owner> a(String n) { return (root, q, cb) -> cb.equal(root.get("name"), n); }
  // rs is a ResultSet: expected 0
  @GetMapping("/s2") public RowMapper<Owner> b() { return (rs, i) -> { rs.getString("x"); return new Owner(); }; }
  @GetMapping("/s3") public Object c() { RowMapper<Row> m = (rs, i) -> { rs.getString("x"); return new Row(); }; return m; }
}
