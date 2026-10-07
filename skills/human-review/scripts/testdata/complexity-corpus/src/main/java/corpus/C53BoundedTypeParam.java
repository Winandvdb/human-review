package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C53BoundedTypeParam {
    @GetMapping("/c53")
    public void h() {
        broadcast(new C26Email());
    }

    <T extends C26Notifier> void broadcast(T n) {
        n.send("x");                           // a call on a type variable bounded by C26Notifier
    }
}
