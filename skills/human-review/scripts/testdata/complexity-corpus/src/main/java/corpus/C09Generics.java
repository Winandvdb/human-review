package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C09Generics {
    private final C09Repo<C09Owner> repo = new C09OwnerRepo();

    @GetMapping("/c09")
    public String h(String id) {
        return repo.load(id).describe();
    }
}
