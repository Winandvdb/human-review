package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C26InterfaceDispatch {
    private final C26Notifier notifier;

    public C26InterfaceDispatch(C26Notifier notifier) {
        this.notifier = notifier;
    }

    @GetMapping("/c26")
    public void h() {
        notifier.send("x");                    // every implementation may run
    }
}
