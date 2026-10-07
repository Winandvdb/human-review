package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C43CommentsAndStrings {
    @GetMapping("/c43")
    public String h() {
        String s = "if (x) { for (;;) {} } && ||";   // if while for: a string, nothing to count
        /* if (a) { while (b) {} } */
        String t = """
                if (y) { switch (z) {} }
                """;
        return s + t;
    }
}
