package corpus;

public interface C15Shape {
    double area();

    default String describe() {
        if (area() > 10) return "big";         // +1
        return "small";
    }

    static C15Shape unit() {
        return new C15Square();
    }
}
