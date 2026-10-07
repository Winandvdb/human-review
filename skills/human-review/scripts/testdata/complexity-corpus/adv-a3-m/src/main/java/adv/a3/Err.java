// From the adversarial review of 7 Oct 2026 (case a3_slf4j).
package adv.a3;
public class Err { public static String error(String m) { if (m == null) { return ""; } return m; } }
