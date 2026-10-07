package corpus;

public class C26Email implements C26Notifier {
    @Override
    public void send(String message) {
        if (message.isBlank()) return;         // +1
        System.out.println(message);
    }
}
