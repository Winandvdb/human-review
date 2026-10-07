package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C24SpringData {
    private final C24Repo repo;

    public C24SpringData(C24Repo repo) {
        this.repo = repo;
    }

    @GetMapping("/c24")
    public Object h() {
        C24Entity e = repo.findById(1L).orElseThrow();
        repo.findByName("x");
        return repo.save(e);
    }
}
