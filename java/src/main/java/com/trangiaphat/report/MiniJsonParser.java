package com.trangiaphat.report;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Small recursive-descent JSON parser with zero external dependencies.
 * Supports the full JSON grammar (objects, arrays, strings, numbers,
 * booleans, null) which is all the report service needs to accept
 * arbitrary "rows" payloads from the Python backend.
 *
 * This is intentionally self-contained rather than pulling in a library
 * such as Jackson/Gson, so the module keeps building with nothing more
 * than a stock JDK (see java/README section in the project README).
 */
public final class MiniJsonParser {

    private final String text;
    private int pos;

    private MiniJsonParser(String text) {
        this.text = text;
        this.pos = 0;
    }

    public static JsonValue parse(String text) {
        MiniJsonParser parser = new MiniJsonParser(text);
        parser.skipWhitespace();
        JsonValue value = parser.parseValue();
        return value;
    }

    private JsonValue parseValue() {
        skipWhitespace();
        if (pos >= text.length()) return JsonValue.ofNull();
        char c = text.charAt(pos);
        switch (c) {
            case '{': return parseObject();
            case '[': return parseArray();
            case '"': return JsonValue.ofString(parseString());
            case 't':
            case 'f': return parseBoolean();
            case 'n': pos += 4; return JsonValue.ofNull();
            default: return parseNumber();
        }
    }

    private JsonValue parseObject() {
        Map<String, JsonValue> map = new LinkedHashMap<>();
        expect('{');
        skipWhitespace();
        if (peek() == '}') { pos++; return JsonValue.ofObject(map); }
        while (true) {
            skipWhitespace();
            String key = parseString();
            skipWhitespace();
            expect(':');
            JsonValue value = parseValue();
            map.put(key, value);
            skipWhitespace();
            if (peek() == ',') { pos++; continue; }
            break;
        }
        skipWhitespace();
        expect('}');
        return JsonValue.ofObject(map);
    }

    private JsonValue parseArray() {
        List<JsonValue> list = new ArrayList<>();
        expect('[');
        skipWhitespace();
        if (peek() == ']') { pos++; return JsonValue.ofArray(list); }
        while (true) {
            JsonValue value = parseValue();
            list.add(value);
            skipWhitespace();
            if (peek() == ',') { pos++; continue; }
            break;
        }
        skipWhitespace();
        expect(']');
        return JsonValue.ofArray(list);
    }

    private String parseString() {
        expect('"');
        StringBuilder sb = new StringBuilder();
        while (pos < text.length() && text.charAt(pos) != '"') {
            char c = text.charAt(pos);
            if (c == '\\' && pos + 1 < text.length()) {
                pos++;
                char esc = text.charAt(pos);
                switch (esc) {
                    case 'n': sb.append('\n'); break;
                    case 't': sb.append('\t'); break;
                    case 'r': sb.append('\r'); break;
                    case '"': sb.append('"'); break;
                    case '\\': sb.append('\\'); break;
                    case '/': sb.append('/'); break;
                    case 'u':
                        String hex = text.substring(pos + 1, pos + 5);
                        sb.append((char) Integer.parseInt(hex, 16));
                        pos += 4;
                        break;
                    default: sb.append(esc);
                }
            } else {
                sb.append(c);
            }
            pos++;
        }
        expect('"');
        return sb.toString();
    }

    private JsonValue parseBoolean() {
        if (text.startsWith("true", pos)) { pos += 4; return JsonValue.ofBoolean(true); }
        if (text.startsWith("false", pos)) { pos += 5; return JsonValue.ofBoolean(false); }
        throw new IllegalArgumentException("Invalid boolean literal at position " + pos);
    }

    private JsonValue parseNumber() {
        int start = pos;
        while (pos < text.length() && "-+.eE0123456789".indexOf(text.charAt(pos)) >= 0) {
            pos++;
        }
        String numStr = text.substring(start, pos);
        return JsonValue.ofNumber(Double.parseDouble(numStr));
    }

    private void skipWhitespace() {
        while (pos < text.length() && Character.isWhitespace(text.charAt(pos))) pos++;
    }

    private char peek() {
        return pos < text.length() ? text.charAt(pos) : '\0';
    }

    private void expect(char c) {
        if (pos >= text.length() || text.charAt(pos) != c) {
            throw new IllegalArgumentException(
                    "Expected '" + c + "' at position " + pos + " but found '" +
                    (pos < text.length() ? text.charAt(pos) : "<eof>") + "'");
        }
        pos++;
    }
}
