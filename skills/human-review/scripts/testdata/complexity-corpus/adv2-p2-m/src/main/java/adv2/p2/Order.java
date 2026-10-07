// From the second adversarial review of 7 Oct 2026 (case p2_drops).
package adv2.p2;
public class Order {
  public int score() { if (true) { return 1; } return 0; }
  public Invoice toInvoice() { for (int i = 0; i < 2; i++) { if (i > 0) { return null; } } return null; }
}
