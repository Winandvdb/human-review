// From the adversarial review of 7 Oct 2026 (case g2_lombok_ctor).
package adv.g2;
import lombok.*;
@Data @NoArgsConstructor
public class Req { private int a; public Req(int a) { this.a = a; } }
