import java.io.BufferedInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

public final class DateMcpServer {
    private static final String PROTOCOL_VERSION = "2024-11-05";
    private static final String DATE_API_BASE_URL = System.getenv().getOrDefault("DATE_API_BASE_URL", "http://127.0.0.1:8091");
    private static final String DATE_API_TOKEN = System.getenv().getOrDefault("DATE_API_TOKEN", "dev-date-token");
    private static final String DATE_API_CLIENT_ID = System.getenv().getOrDefault("DATE_API_CLIENT_ID", "mcp-date-client");
    private static final HttpClient HTTP_CLIENT = HttpClient.newHttpClient();

    private DateMcpServer() {
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

    private static String handleRequest(String json) {
        String method = extractJsonString(json, "method");
        String id = extractJsonRaw(json, "id");

        if ("notifications/initialized".equals(method)) {
            return null;
        }

        if ("initialize".equals(method)) {
            return success(id, "{\"protocolVersion\":\"" + PROTOCOL_VERSION + "\",\"capabilities\":{\"tools\":{},\"resources\":{},\"prompts\":{}},\"serverInfo\":{\"name\":\"date-java-mcp\",\"version\":\"0.1.0\"}}");
        }

        if ("tools/list".equals(method)) {
            return success(id, "{"
                + "\"tools\":["
                + "{"
                + "\"name\":\"get_current_time\","
                + "\"description\":\"Obtiene la hora actual de una ubicación soportada sin exponer auth headers al cliente.\","
                + "\"inputSchema\":{\"type\":\"object\",\"properties\":{\"location\":{\"type\":\"string\",\"description\":\"Código de ubicación, por ejemplo us o mx-central.\"},\"ip\":{\"type\":\"string\",\"description\":\"IP opcional para reenviar al backend.\"}},\"additionalProperties\":false}"
                + "},"
                + "{"
                + "\"name\":\"list_supported_locations\","
                + "\"description\":\"Devuelve las ubicaciones soportadas por el servicio date.\","
                + "\"inputSchema\":{\"type\":\"object\",\"properties\":{},\"additionalProperties\":false}"
                + "}"
                + "]"
                + "}");
        }

        if ("tools/call".equals(method)) {
            String toolName = extractJsonString(json, "name");
            if ("get_current_time".equals(toolName)) {
                String location = extractJsonString(json, "location");
                String ip = extractJsonString(json, "ip");
                String payload = callApi("/date/time", "location", location, ip);
                return toolResult(id, payload);
            }
            if ("list_supported_locations".equals(toolName)) {
                return toolResult(id, callApi("/date/locations", null, null, null));
            }
            return error(id, -32602, "Herramienta no soportada: " + toolName);
        }

        if ("resources/list".equals(method)) {
            return success(id, callApi("/date/resources", null, null, null));
        }

        if ("resources/read".equals(method)) {
            String uri = extractJsonString(json, "uri");
            String path = resourcePath(uri);
            if (path == null) {
                return error(id, -32602, "Resource no soportado: " + uri);
            }
            return success(id, callApi(path, null, null, null));
        }

        if ("prompts/list".equals(method)) {
            return success(id, callApi("/date/prompts", null, null, null));
        }

        if ("prompts/get".equals(method)) {
            String promptName = extractJsonString(json, "name");
            String fromLocation = extractJsonString(json, "from_location");
            String toLocation = extractJsonString(json, "to_location");
            String location = extractJsonString(json, "location");
            String path = promptPath(promptName, location, fromLocation, toLocation);
            if (path == null) {
                return error(id, -32602, "Prompt no soportado: " + promptName);
            }
            return success(id, callApi(path, null, null, null));
        }

        return error(id, -32601, "Método no encontrado: " + method);
    }

    private static String toolResult(String id, String payload) {
        return success(id, "{\"content\":[{\"type\":\"text\",\"text\":" + quote(payload) + "}],\"structuredContent\":" + payload + ",\"isError\":false}");
    }

    private static String success(String id, String resultJson) {
        return "{\"jsonrpc\":\"2.0\",\"id\":" + (id == null ? "null" : id) + ",\"result\":" + resultJson + "}";
    }

    private static String error(String id, int code, String message) {
        return "{\"jsonrpc\":\"2.0\",\"id\":" + (id == null ? "null" : id) + ",\"error\":{\"code\":" + code + ",\"message\":" + quote(message) + "}}";
    }

    private static String callApi(String path, String queryKey, String queryValue, String ip) {
        try {
            StringBuilder url = new StringBuilder(DATE_API_BASE_URL).append(path);
            if (queryKey != null && queryValue != null && !queryValue.isBlank()) {
                url.append("?").append(URLEncoder.encode(queryKey, StandardCharsets.UTF_8)).append("=")
                    .append(URLEncoder.encode(queryValue, StandardCharsets.UTF_8));
            }
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(url.toString()))
                .header("Authorization", "Bearer " + DATE_API_TOKEN)
                .header("X-Date-Client", DATE_API_CLIENT_ID)
                .GET();
            if (ip != null && !ip.isBlank()) {
                builder.header("X-Forwarded-For", ip);
            }
            HttpResponse<String> response = HTTP_CLIENT.send(builder.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() != 200) {
                throw new IllegalStateException("Date REST backend responded with HTTP " + response.statusCode() + ": " + response.body());
            }
            return response.body();
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Date REST backend unavailable at " + DATE_API_BASE_URL, exception);
        } catch (IOException exception) {
            throw new IllegalStateException("Date REST backend unavailable at " + DATE_API_BASE_URL, exception);
        }
    }

    private static String resourcePath(String uri) {
        if ("date://auth-reference".equals(uri)) {
            return "/date/resources/auth-reference";
        }
        if ("date://location-reference".equals(uri)) {
            return "/date/resources/location-reference";
        }
        return null;
    }

    private static String promptPath(String promptName, String location, String fromLocation, String toLocation) {
        if ("single-location-time".equals(promptName)) {
            if (location == null || location.isBlank()) {
                return "/date/prompts/single-location-time";
            }
            return "/date/prompts/single-location-time?location=" + URLEncoder.encode(location, StandardCharsets.UTF_8);
        }
        if ("compare-locations".equals(promptName)) {
            StringBuilder path = new StringBuilder("/date/prompts/compare-locations");
            boolean first = true;
            first = appendQuery(path, "from_location", fromLocation, first);
            appendQuery(path, "to_location", toLocation, first);
            return path.toString();
        }
        return null;
    }

    private static boolean appendQuery(StringBuilder path, String key, String value, boolean first) {
        if (value == null || value.isBlank()) {
            return first;
        }
        path.append(first ? "?" : "&");
        path.append(URLEncoder.encode(key, StandardCharsets.UTF_8));
        path.append("=");
        path.append(URLEncoder.encode(value, StandardCharsets.UTF_8));
        return false;
    }

    private static void writeMessage(String json) throws IOException {
        byte[] body = json.getBytes(StandardCharsets.UTF_8);
        System.out.write(("Content-Length: " + body.length + "\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        System.out.write(body);
        System.out.flush();
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
            if (line.toLowerCase().startsWith("content-length:")) {
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
                    builder.append((char) next).append((char) following);
                }
                continue;
            }
            if (next == '\n') {
                return builder.toString();
            }
            builder.append((char) next);
        }
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
        String pattern = "\"" + key + "\"";
        int keyIndex = json.indexOf(pattern);
        if (keyIndex < 0) {
            return null;
        }
        int colon = json.indexOf(':', keyIndex + pattern.length());
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
        int keyIndex = json.indexOf(pattern);
        if (keyIndex < 0) {
            return null;
        }
        int colon = json.indexOf(':', keyIndex + pattern.length());
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
