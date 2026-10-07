// From the third adversarial review of 7 Oct 2026 (case q1).
package adv3.q1.x;
import org.springframework.batch.item.ItemProcessor;
public class OrderToInvoice implements ItemProcessor<Order, Invoice> {
  public Invoice process(Order o) { return new Invoice(); }
}
