package com.trangiaphat.report;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Minimal, dependency-free JSON value representation used by
 * {@link MiniJsonParser}. Only the subset of JSON needed by the report
 * service is supported: objects, arrays, strings, numbers, booleans, null.
 */
public final class JsonValue {

    public enum Type { OBJECT, ARRAY, STRING, NUMBER, BOOLEAN, NULL }

    public final Type type;
    private final Map<String, JsonValue> objectValue;
    private final List<JsonValue> arrayValue;
    private final String stringValue;
    private final double numberValue;
    private final boolean booleanValue;

    private JsonValue(Type type, Map<String, JsonValue> objectValue, List<JsonValue> arrayValue,
                       String stringValue, double numberValue, boolean booleanValue) {
        this.type = type;
        this.objectValue = objectValue;
        this.arrayValue = arrayValue;
        this.stringValue = stringValue;
        this.numberValue = numberValue;
        this.booleanValue = booleanValue;
    }

    public static JsonValue ofObject(Map<String, JsonValue> map) {
        return new JsonValue(Type.OBJECT, map, null, null, 0, false);
    }

    public static JsonValue ofArray(List<JsonValue> list) {
        return new JsonValue(Type.ARRAY, null, list, null, 0, false);
    }

    public static JsonValue ofString(String s) {
        return new JsonValue(Type.STRING, null, null, s, 0, false);
    }

    public static JsonValue ofNumber(double d) {
        return new JsonValue(Type.NUMBER, null, null, null, d, false);
    }

    public static JsonValue ofBoolean(boolean b) {
        return new JsonValue(Type.BOOLEAN, null, null, null, 0, b);
    }

    public static JsonValue ofNull() {
        return new JsonValue(Type.NULL, null, null, null, 0, false);
    }

    public Map<String, JsonValue> asObject() {
        return objectValue == null ? new LinkedHashMap<>() : objectValue;
    }

    public List<JsonValue> asArray() {
        return arrayValue;
    }

    public String asString() {
        if (type == Type.STRING) return stringValue;
        if (type == Type.NUMBER) {
            // Render integers without a trailing ".0"
            if (numberValue == Math.floor(numberValue) && !Double.isInfinite(numberValue)) {
                return String.valueOf((long) numberValue);
            }
            return String.valueOf(numberValue);
        }
        if (type == Type.BOOLEAN) return String.valueOf(booleanValue);
        if (type == Type.NULL) return "";
        return "";
    }

    public double asNumber() {
        return numberValue;
    }
}
