// From the second adversarial review of 7 Oct 2026 (case p2_drops).
package adv2.p2;
import org.springframework.web.bind.annotation.*;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.retry.support.RetryTemplate;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Flux;
import java.util.function.Consumer;
@RestController
public class C {
  private final RetryTemplate retryTemplate = new RetryTemplate();
  private final PriceCalculator calculator = new PriceCalculator();
  // expected Order.score = 1
  @GetMapping("/d1") public Mono<Integer> a(Order order) { return Mono.just(order).map(x -> x.score()); }
  // expected Order.score = 1
  @GetMapping("/d2") public Flux<Integer> b(java.util.List<Order> orders) { return Flux.fromIterable(orders).map(o -> o.score()); }
  // expected Order.toInvoice = 3
  @GetMapping("/d3") public Object c(Order order) throws Exception { ItemProcessor<Order, Invoice> p = o -> o.toInvoice(); return p.process(order); }
  // expected PriceCalculator.apply = 2 (+ withRetry 0)
  @GetMapping("/d4") public void d(Order order) { withRetry(retryTemplate, calc -> calc.apply(order)); }
  void withRetry(RetryTemplate rt, Consumer<PriceCalculator> c) { c.accept(calculator); }
}
