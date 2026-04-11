import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class HelloService {
    private static final Map<String, String> GREETINGS = Map.of(
        "en", "Hello",
        "zh", "Ni hao",
        "hi", "Namaste",
        "es", "Hola",
        "fr", "Bonjour",
        "ar", "Marhaban",
        "bn", "Nomoskar",
        "pt", "Ola",
        "ru", "Privet",
        "ur", "Assalam o Alaikum"
    );

    private HelloService() {
    }

    public static List<String> getSupportedLanguages() {
        return GREETINGS.keySet().stream().sorted().toList();
    }

    public static int getSupportedLanguageCount() {
        return GREETINGS.size();
    }

    public static Map<String, Object> buildHelloPayload(String name, String lang, String ip) {
        String normalizedLang = normalizeLang(lang);
        String greeting = GREETINGS.get(normalizedLang);
        String timestamp = ZonedDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ofPattern("HH:mm:ss 'UTC+00:00'"));

        Map<String, Object> payload = new LinkedHashMap<>();
        if (name != null && !name.isBlank()) {
            payload.put("message", greeting + " " + name + "!");
            payload.put("timestamp", timestamp);
            payload.put("ip", ip);
            payload.put("lang", normalizedLang);
            payload.put("has_name", true);
            payload.put("name", name);
            return payload;
        }

        payload.put("message", greeting + "!");
        payload.put("timestamp", timestamp);
        payload.put("ip", ip);
        payload.put("lang", normalizedLang);
        payload.put("has_name", false);
        return payload;
    }

    public static String normalizeLang(String lang) {
        if (lang == null || lang.isBlank()) {
            return "en";
        }
        String normalized = lang.trim().toLowerCase(Locale.ROOT);
        if (GREETINGS.containsKey(normalized)) {
            return normalized;
        }
        return "en";
    }
}
