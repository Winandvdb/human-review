package corpus;

import java.io.IOException;
import java.io.StringReader;
import org.springframework.web.bind.annotation.*;

@RestController
public class C22TryWithResources {
    @GetMapping("/c22")
    public int h(String s, boolean x) {
        try (StringReader r = new StringReader(s)) {
            if (x) {                           // +1: try does not nest
                return r.read();
            }
        } catch (IOException e) {              // +1
            return -1;
        } finally {
            if (x) System.out.println("done"); // +1
        }
        return 0;
    }
}
