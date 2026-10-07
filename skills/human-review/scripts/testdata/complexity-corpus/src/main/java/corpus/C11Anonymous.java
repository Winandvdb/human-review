package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C11Anonymous {
    boolean flag;

    @GetMapping("/c11")
    public void h() {
        Runnable r = new Runnable() {
            @Override
            public void run() {
                if (flag) {                    // +2: a method nested in the handler (white paper)
                    System.out.println("x");
                }
            }
        };
        r.run();
    }
}
