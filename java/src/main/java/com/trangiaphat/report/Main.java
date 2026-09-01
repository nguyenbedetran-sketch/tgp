package com.trangiaphat.report;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Tran Gia Phat Report Service (Java).
 *
 * A standalone data/reporting module the Python backend calls as a
 * subprocess to export business data (projects, consultation leads,
 * estimates) to CSV or a formatted JSON report. Demonstrates a real,
 * independent Java service with its own request/response contract rather
 * than a decorative stub.
 *
 * Contract:
 *   stdin  -> a single JSON object:
 *             {
 *               "title":   "Danh sach du an",
 *               "format":  "csv" | "json",
 *               "columns": ["id","name","location","area_m2","year"],   // optional for csv
 *               "rows":    [ { "id": 1, "name": "...", ... }, ... ]
 *             }
 *   stdout -> the rendered report (CSV text or JSON text)
 *   exit code 0 on success, 1 on error (message printed to stderr)
 *
 * Build:  mvn -q -f java/pom.xml package
 * Run:    java -jar java/target/tgp-report-service.jar < payload.json
 */
public final class Main {

    public static void main(String[] args) {
        try {
            String input = readAll(System.in);
            JsonValue root = MiniJsonParser.parse(input);
            Map<String, JsonValue> obj = root.asObject();

            String title = obj.containsKey("title") ? obj.get("title").asString() : "Bao cao";
            String format = obj.containsKey("format") ? obj.get("format").asString() : "json";

            List<String> columns = new ArrayList<>();
            if (obj.containsKey("columns") && obj.get("columns").type == JsonValue.Type.ARRAY) {
                for (JsonValue v : obj.get("columns").asArray()) columns.add(v.asString());
            }

            List<JsonValue> rows = new ArrayList<>();
            if (obj.containsKey("rows") && obj.get("rows").type == JsonValue.Type.ARRAY) {
                rows = obj.get("rows").asArray();
            }

            String output;
            if ("csv".equalsIgnoreCase(format)) {
                output = ReportGenerator.toCsv(title, columns, rows);
            } else {
                output = ReportGenerator.toJsonReport(title, rows);
            }

            System.out.print(output);
            System.out.flush();
        } catch (Exception e) {
            System.err.println("Report generation failed: " + e.getMessage());
            System.exit(1);
        }
    }

    private static String readAll(java.io.InputStream in) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
            }
        }
        return sb.toString();
    }
}
