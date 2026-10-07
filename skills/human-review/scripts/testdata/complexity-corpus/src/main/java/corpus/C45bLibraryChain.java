package corpus;

import com.example.lib.Registry;
import org.springframework.web.bind.annotation.*;

@RestController
public class C45bLibraryChain {
    @GetMapping("/c45b")
    public void h() {
        var t = Registry.lookup("k").current();
        t.process();                           // nothing of this project in the chain: a library value, dropped
    }
}
