// From the third adversarial review of 7 Oct 2026 (case q1).
package adv3.q1.x;
import org.springframework.core.convert.converter.Converter;
public class IdToOrder implements Converter<String, Order> {
  public Order convert(String s) { return new Order(); }
}
