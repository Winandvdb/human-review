// From the adversarial review of 7 Oct 2026 (case f2_iface_classpath).
package adv.f2;
import org.springframework.web.bind.annotation.*;
public interface OwnerApi { @GetMapping("/owners") String list(); }
