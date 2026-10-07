package corpus;

import org.springframework.web.bind.annotation.*;

@RestController
public class C29LabeledBreak {
    @GetMapping("/c29")
    public int h(int[][] grid, int target) {
        int found = -1;
        outer:
        for (int[] row : grid) {               // +1
            for (int v : row) {                // +2
                if (v == target) {             // +3
                    found = v;
                    break outer;               // +1
                }
            }
        }
        return found;
    }
}
