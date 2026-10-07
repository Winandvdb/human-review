// From the third adversarial review of 7 Oct 2026 (case q2_spec).
package adv3.q2.x;
public class Owner { public String getName() { return "a"; } public int get(String k) { if (k == null) { return 0; } return 1; } }
