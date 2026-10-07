package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(C37ConstantPath.BASE)
public class C37ConstantPath {
    static final String BASE = "/api/c37";

    @GetMapping("/x")
    public int h(int a) {
        return a > 0 ? a : 0;                  // +1
    }

    @RequestMapping(value = "/y", method = RequestMethod.DELETE)
    public void del() {
    }
}
