// From the second adversarial review of 7 Oct 2026 (case p1_payload).
package adv2.p1;
public class Post {
  public String getContent() { if (true) { return "a"; } return "b"; }
  public boolean isEmpty() { for (int i = 0; i < 3; i++) { if (i > 1) { return true; } } return false; }
  public int check() { if (true) { return 1; } return 0; }
}
