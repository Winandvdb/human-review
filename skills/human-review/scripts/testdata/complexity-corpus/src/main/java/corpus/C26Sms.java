package corpus;

public class C26Sms implements C26Notifier {
    @Override
    public void send(String message) {
        for (String part : message.split(" ")) {   // +1
            if (part.length() > 160) {              // +2
                throw new IllegalStateException();
            }
        }
    }
}
