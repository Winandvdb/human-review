// From the third adversarial review of 7 Oct 2026 (case q1).
package adv3.q1.x;
import org.springframework.web.bind.annotation.*;
import org.modelmapper.ModelMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Mono;
import org.springframework.retry.support.RetryTemplate;
import java.util.*;
import java.util.function.*;
@RestController
public class C {
  private final ModelMapper mm = new ModelMapper();
  private final ObjectMapper om = new ObjectMapper();
  private final OrderToInvoice proc = new OrderToInvoice();
  private final IdToOrder conv = new IdToOrder();
  private final RetryTemplate rt = new RetryTemplate();
  OrderDto toDto(Order o) { return null; }
  // DTO getter is Lombok: expected 0 (Order.getTotal=2 must NOT be followed)
  @GetMapping("/q1") public int a(Order o) { return mm.map(o, OrderDto.class).getTotal(); }
  @GetMapping("/q2") public int b(Order o) { return om.convertValue(o, OrderDto.class).getTotal(); }
  // d is an OrderDto: expected toDto 0 + nothing => 0
  @GetMapping("/q3") public Mono<Integer> c(Order o) { return Mono.just(o).map(x -> toDto(x)).map(d -> d.getTotal()); }
  // process returns Invoice: expected process 0 + Invoice.send 1 = 1
  @GetMapping("/q4") public void d(Order o) throws Exception { proc.process(o).send(); }
  // convert returns Order: expected Order.score 1
  @GetMapping("/q5") public int e(String s) { return conv.convert(s).score(); }
  // generic project callee + library arg: expected each 0 + Order.score 1
  @GetMapping("/q6") public void f(List<Order> orders) { each(orders, rt, o -> o.score()); }
  <T> void each(List<T> items, RetryTemplate r, Consumer<T> c) { items.forEach(c); }
}
