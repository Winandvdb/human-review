package corpus;

import com.example.lib.LibraryBase;
import org.springframework.web.bind.annotation.*;

@RestController
public class C45UnknownReceiver extends LibraryBase {
    @GetMapping("/c45")
    public void h() {
        helper.process();                      // `helper` is a field of a library superclass: its type is unknowable,
    }                                          // and this project declares a `process` — report it, never guess
}
