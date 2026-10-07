package corpus;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springaicommunity.mcp.annotation.McpTool;

public class C38OtherEntries {
    @McpTool(name = "c38_tool", description = "a tool")
    public String tool(String q) {
        if (q == null) return "";              // +1
        return q;
    }

    @Scheduled(fixedRate = 1000)
    public void tick() {
        for (int i = 0; i < 3; i++) {          // +1
            System.out.println(i);
        }
    }

    @KafkaListener(topics = "c38-topic")
    public void onMessage(String m) {
        while (m.isEmpty()) {                  // +1
            m = "x";
        }
    }
}
