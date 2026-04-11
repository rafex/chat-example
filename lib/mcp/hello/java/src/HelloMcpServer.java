import java.io.BufferedInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

public final class HelloMcpServer {
    private static final String PROTOCOL_VERSION = "2024-11-05";
    private static final String HELLO_API_BASE_URL =
        System.getenv().getOrDefault("HELLO_API_BASE_URL", "http://127.0.0.1:8081");
    private static final HttpClient HTTP_CLIENT = HttpClient.newHttpClient();

    private HelloMcpServer() {
    }

    public static void main(String[] args) throws IOException {
        BufferedInputStream input = new BufferedInputStream(System.in);
        while (true) {
            String message = readMessage(input);
            if (message == null) {
                return;
            }
            String response = handleRequest(message);
            if (response != null) {
                writeMessage(response);
            }
        }
    }

    private static String readMessage(BufferedInputStream input) throws IOException {
        Integer contentLength = null;
        while (true) {
            String line = readHeaderLine(input);
            if (line == null) {
                return null;
            }
            if (line.isEmpty()) {
                break;
            }
            String lower = line.toLowerCase();
            if (lower.startsWith("content-length:")) {
                contentLength = Integer.parseInt(line.substring(line.indexOf(':') + 1).trim());
            }
        }

        if (contentLength == null) {
            return null;
        }

        byte[] body = input.readNBytes(contentLength);
        if (body.length == 0) {
            return null;
        }
        return new String(body, StandardCharsets.UTF_8);
    }

    private static String readHeaderLine(BufferedInputStream input) throws IOException {
        StringBuilder builder = new StringBuilder();
        while (true) {
            int next = input.read();
            if (next == -1) {
                if (builder.isEmpty()) {
                    return null;
                }
                throw new EOFException("Unexpected EOF while reading MCP header");
            }
            if (next == '\r') {
                int following = input.read();
                if (following == '\n') {
                    return builder.toString();
                }
                if (following != -1) {
                    builder.append((char) next);
                    builder.append((char) following);
                }
                continue;
            }
            if (next == '\n') {
                return builder.toString();
            }
            builder.append((char) next);
        }
    }

    private static void writeMessage(String json) throws IOException {
        byte[] body = json.getBytes(StandardCharsets.UTF_8);
        String header = "Content-Length: " + body.length + "\r\n\r\n";
        System.out.write(header.getBytes(StandardCharsets.UTF_8));
        System.out.write(body);
        System.out.flush();
    }

    private static String handleRequest(String json) {
        String method = extractJsonString(json, "method");
        String id = extractJsonRaw(json, "id");

        if ("notifications/initialized".equals(method)) {
            return null;
        }

        if ("initialize".equals(method)) {
            String result = "{"
                + "\"protocolVersion\":\"" + PROTOCOL_VERSION + "\","
                + "\"capabilities\":{\"tools\":{},\"resources\":{},\"prompts\":{}},"
                + "\"serverInfo\":{\"name\":\"hello-java-mcp\",\"version\":\"0.1.0\"}"
                + "}";
            return success(id, result);
        }

        if ("tools/list".equals(method)) {
            String result = "{"
                + "\"tools\":[{"
                + "\"name\":\"say_hello\","
                + "\"description\":\"Devuelve un saludo opcionalmente personalizado y localizado en uno de los 10 idiomas soportados.\","
                + "\"inputSchema\":{"
                + "\"type\":\"object\","
                + "\"properties\":{"
                + "\"name\":{\"type\":\"string\",\"description\":\"Nombre opcional a saludar.\"},"
                + "\"lang\":{\"type\":\"string\",\"description\":\"Idioma del saludo, por ejemplo en o es.\"},"
                + "\"ip\":{\"type\":\"string\",\"description\":\"IP opcional a reflejar en la respuesta.\"}"
                + "},"
                + "\"additionalProperties\":false"
                + "}"
                + "},{"
                + "\"name\":\"get_hello_languages\","
                + "\"description\":\"Devuelve la cantidad de idiomas soportados y sus códigos.\","
                + "\"inputSchema\":{"
                + "\"type\":\"object\","
                + "\"properties\":{},"
                + "\"additionalProperties\":false"
                + "}"
                + "}]"
                + "}";
            return success(id, result);
        }

        if ("tools/call".equals(method)) {
            String toolName = extractJsonString(json, "name");
            if ("get_hello_languages".equals(toolName)) {
                String payloadJson = callHelloLanguagesApi();
                String result = "{"
                    + "\"content\":[{\"type\":\"text\",\"text\":" + quote(payloadJson) + "}],"
                    + "\"structuredContent\":" + payloadJson + ","
                    + "\"isError\":false"
                    + "}";
                return success(id, result);
            }

            if (!"say_hello".equals(toolName)) {
                return error(id, -32602, "Herramienta no soportada: " + toolName);
            }

            String name = extractJsonString(json, "name", 2);
            String lang = extractJsonString(json, "lang");
            String ip = extractJsonString(json, "ip");
            if (ip == null || ip.isBlank()) {
                ip = "127.0.0.1";
            }

            String payloadJson = callHelloApi(name, lang, ip);
            String result = "{"
                + "\"content\":[{\"type\":\"text\",\"text\":" + quote(payloadJson) + "}],"
                + "\"structuredContent\":" + payloadJson + ","
                + "\"isError\":false"
                + "}";
            return success(id, result);
        }

        if ("resources/list".equals(method)) {
            return success(id, callApi("/hello/resources"));
        }

        if ("resources/read".equals(method)) {
            String resourceUri = extractJsonString(json, "uri");
            String path = mapResourceUriToPath(resourceUri);
            if (path == null) {
                return error(id, -32602, "Resource no soportado: " + resourceUri);
            }
            return success(id, callApi(path));
        }

        if ("prompts/list".equals(method)) {
            return success(id, callApi("/hello/prompts"));
        }

        if ("prompts/get".equals(method)) {
            String promptName = extractJsonString(json, "name");
            String argumentName = extractJsonString(json, "name", 2);
            String argumentLang = extractJsonString(json, "lang");
            String path = buildPromptPath(promptName, argumentName, argumentLang);
            if (path == null) {
                return error(id, -32602, "Prompt no soportado: " + promptName);
            }
            return success(id, callApi(path));
        }

        return error(id, -32601, "Método no encontrado: " + method);
    }

    private static String success(String id, String resultJson) {
        return "{"
            + "\"jsonrpc\":\"2.0\","
            + "\"id\":" + normalizeId(id) + ","
            + "\"result\":" + resultJson
            + "}";
    }

    private static String error(String id, int code, String message) {
        return "{"
            + "\"jsonrpc\":\"2.0\","
            + "\"id\":" + normalizeId(id) + ","
            + "\"error\":{\"code\":" + code + ",\"message\":" + quote(message) + "}"
            + "}";
    }

    private static String normalizeId(String id) {
        if (id == null || id.isBlank()) {
            return "null";
        }
        return id;
    }

    private static String callHelloApi(String name, String lang, String ip) {
        try {
            StringBuilder url = new StringBuilder(HELLO_API_BASE_URL).append("/hello");
            boolean first = true;
            first = appendQuery(url, "name", name, first);
            appendQuery(url, "lang", lang, first);

            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url.toString()))
                .header("X-Forwarded-For", ip == null || ip.isBlank() ? "127.0.0.1" : ip)
                .GET()
                .build();

            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() != 200) {
                throw new IllegalStateException(
                    "REST backend responded with HTTP " + response.statusCode() + ": " + response.body()
                );
            }
            return response.body();
        } catch (IOException | InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("REST backend unavailable at " + HELLO_API_BASE_URL, exception);
        }
    }

    private static boolean appendQuery(StringBuilder url, String key, String value, boolean first) {
        if (value == null || value.isBlank()) {
            return first;
        }
        url.append(first ? "?" : "&");
        url.append(URLEncoder.encode(key, StandardCharsets.UTF_8));
        url.append("=");
        url.append(URLEncoder.encode(value, StandardCharsets.UTF_8));
        return false;
    }

    private static String callHelloLanguagesApi() {
        return callApi("/hello/languages");
    }

    private static String callApi(String path) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(HELLO_API_BASE_URL + path))
                .GET()
                .build();

            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() != 200) {
                throw new IllegalStateException(
                    "REST backend responded with HTTP " + response.statusCode() + ": " + response.body()
                );
            }
            return response.body();
        } catch (IOException | InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("REST backend unavailable at " + HELLO_API_BASE_URL, exception);
        }
    }

    private static String mapResourceUriToPath(String resourceUri) {
        if ("hello://service-overview".equals(resourceUri)) {
            return "/hello/resources/service-overview";
        }
        if ("hello://language-reference".equals(resourceUri)) {
            return "/hello/resources/language-reference";
        }
        return null;
    }

    private static String buildPromptPath(String promptName, String name, String lang) {
        if ("greet-user".equals(promptName)) {
            StringBuilder path = new StringBuilder("/hello/prompts/greet-user");
            boolean first = true;
            first = appendQuery(path, "name", name, first);
            appendQuery(path, "lang", lang, first);
            return path.toString();
        }
        if ("language-report".equals(promptName)) {
            StringBuilder path = new StringBuilder("/hello/prompts/language-report");
            appendQuery(path, "name", name, true);
            return path.toString();
        }
        return null;
    }

    private static String quote(String value) {
        return "\"" + escapeJson(value) + "\"";
    }

    private static String escapeJson(String value) {
        StringBuilder builder = new StringBuilder();
        for (char current : value.toCharArray()) {
            switch (current) {
                case '\\' -> builder.append("\\\\");
                case '"' -> builder.append("\\\"");
                case '\n' -> builder.append("\\n");
                case '\r' -> builder.append("\\r");
                case '\t' -> builder.append("\\t");
                default -> builder.append(current);
            }
        }
        return builder.toString();
    }

    private static String extractJsonString(String json, String key) {
        return extractJsonString(json, key, 1);
    }

    private static String extractJsonString(String json, String key, int occurrence) {
        String pattern = "\"" + key + "\"";
        int fromIndex = 0;
        int foundAt = -1;
        for (int i = 0; i < occurrence; i++) {
            foundAt = json.indexOf(pattern, fromIndex);
            if (foundAt < 0) {
                return null;
            }
            fromIndex = foundAt + pattern.length();
        }

        int colon = json.indexOf(':', foundAt);
        if (colon < 0) {
            return null;
        }

        int valueStart = colon + 1;
        while (valueStart < json.length() && Character.isWhitespace(json.charAt(valueStart))) {
            valueStart++;
        }

        if (valueStart >= json.length() || json.charAt(valueStart) != '"') {
            return null;
        }

        StringBuilder builder = new StringBuilder();
        for (int i = valueStart + 1; i < json.length(); i++) {
            char current = json.charAt(i);
            if (current == '"' && json.charAt(i - 1) != '\\') {
                return builder.toString()
                    .replace("\\\"", "\"")
                    .replace("\\n", "\n")
                    .replace("\\r", "\r")
                    .replace("\\t", "\t")
                    .replace("\\\\", "\\");
            }
            builder.append(current);
        }
        return null;
    }

    private static String extractJsonRaw(String json, String key) {
        String pattern = "\"" + key + "\"";
        int foundAt = json.indexOf(pattern);
        if (foundAt < 0) {
            return null;
        }

        int colon = json.indexOf(':', foundAt);
        if (colon < 0) {
            return null;
        }

        int valueStart = colon + 1;
        while (valueStart < json.length() && Character.isWhitespace(json.charAt(valueStart))) {
            valueStart++;
        }

        int valueEnd = valueStart;
        while (valueEnd < json.length() && ",}\r\n".indexOf(json.charAt(valueEnd)) < 0) {
            valueEnd++;
        }
        return json.substring(valueStart, valueEnd).trim();
    }
}
