package corpus;

import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;
import org.springframework.web.bind.annotation.*;

@RestController
public class C42AnnotatedParams {
    @GetMapping("/c42")
    public String h(@RequestParam(name = "q", defaultValue = "x") String q,
                    @Parameter(schema = @Schema(allowableValues = {"a", "b"})) String s) {
        if (q.isEmpty()) return s;             // +1
        return q;
    }
}
