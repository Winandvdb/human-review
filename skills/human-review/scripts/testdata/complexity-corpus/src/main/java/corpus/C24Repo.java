package corpus;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface C24Repo extends JpaRepository<C24Entity, Long> {
    List<C24Entity> findByName(String name);
}
