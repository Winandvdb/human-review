// From the third adversarial review of 7 Oct 2026 (case q1).
package adv3.q1.x;
public class Order {
  public int getTotal() { int t = 0; for (int i = 0; i < 3; i++) { if (i > 1) { t++; } } return t; }
  public int score() { if (true) { return 1; } return 0; }
}
