// From the adversarial review of 7 Oct 2026 (case g1_libnoise).
package adv.g1;
import org.springframework.web.bind.annotation.*;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import com.google.common.base.Splitter;
import static com.google.common.base.Splitter.on;
@RestController
public class C {
  private static final Splitter onPipe = on('|');
  private final Splitter onComma = Splitter.on(',');
  @GetMapping("/g1") public Object a(String s) {
    final MapSqlParameterSource params = new MapSqlParameterSource();
    params.addValue("a", 1);
    MapSqlParameterSource p2 = new MapSqlParameterSource();
    p2.addValue("b", 2);
    onPipe.split(s);
    onComma.split(s);
    return params;
  }
}
