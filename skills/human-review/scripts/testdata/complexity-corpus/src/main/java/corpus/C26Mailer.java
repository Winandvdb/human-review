package corpus;

/** Has a `send` too, but is no C26Notifier: dispatch must not reach it. */
public class C26Mailer {
    public void send(String to) {
        if (to == null) return;                // +1, never reached
        System.out.println(to);
    }
}
