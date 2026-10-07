// From the second adversarial review of 7 Oct 2026 (case p3_ids).
package adv2.p3;
public record OwnerId(long a, long b) { public boolean isValid() { for (int i = 0; i < 2; i++) { while (a > b) { if (a > 0) { return true; } } } return false; } }
