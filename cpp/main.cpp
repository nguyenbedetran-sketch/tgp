// main.cpp
// Tran Gia Phat - Construction cost estimation engine (C++)
//
// CLI wrapper around calculator.{h,cpp}. Reads a single-line, FLAT JSON
// object from stdin (only string/number values, no nesting/arrays) and
// writes a single-line flat JSON object with the computed result to stdout.
//
// This module deliberately avoids any third-party JSON library so it can be
// built with nothing but a C++17 compiler. The parser below only needs to
// support the small, well-defined schema used by the estimate form - it is
// not a general purpose JSON parser.
//
// Usage:
//   echo '{"construction_type":"biet_thu","land_area_m2":200,...}' | ./tgp_calculator
//
// Exit codes:
//   0  success, result JSON printed to stdout
//   1  invalid input, error JSON printed to stdout ({"valid":false,...})

#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

#include "calculator.h"

namespace {

std::string read_all_stdin() {
    std::ostringstream ss;
    ss << std::cin.rdbuf();
    return ss.str();
}

// Extremely small flat-JSON parser: {"key":"value","key2":123, ...}
// Supports string values (double-quoted, backslash-escaped) and bare
// numeric values. Good enough for the controlled input this CLI receives
// from the Python backend.
std::map<std::string, std::string> parse_flat_json(const std::string& text) {
    std::map<std::string, std::string> out;
    size_t i = 0;
    const size_t n = text.size();

    auto skip_ws = [&]() {
        while (i < n && std::isspace(static_cast<unsigned char>(text[i]))) ++i;
    };

    auto parse_string = [&]() -> std::string {
        std::string s;
        if (i < n && text[i] == '"') {
            ++i;
            while (i < n && text[i] != '"') {
                if (text[i] == '\\' && i + 1 < n) {
                    ++i;
                    s += text[i];
                } else {
                    s += text[i];
                }
                ++i;
            }
            if (i < n) ++i;  // closing quote
        }
        return s;
    };

    skip_ws();
    if (i < n && text[i] == '{') ++i;

    while (i < n) {
        skip_ws();
        if (i >= n || text[i] == '}') break;
        if (text[i] != '"') { ++i; continue; }
        std::string key = parse_string();
        skip_ws();
        if (i < n && text[i] == ':') ++i;
        skip_ws();

        std::string value;
        if (i < n && text[i] == '"') {
            value = parse_string();
        } else {
            size_t start = i;
            while (i < n && text[i] != ',' && text[i] != '}') ++i;
            value = text.substr(start, i - start);
            // trim whitespace
            while (!value.empty() && std::isspace(static_cast<unsigned char>(value.front())))
                value.erase(value.begin());
            while (!value.empty() && std::isspace(static_cast<unsigned char>(value.back())))
                value.pop_back();
        }
        out[key] = value;

        skip_ws();
        if (i < n && text[i] == ',') ++i;
    }

    return out;
}

std::string json_escape(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"' || c == '\\') out += '\\';
        out += c;
    }
    return out;
}

}  // namespace

int main() {
    const std::string raw = read_all_stdin();
    const auto fields = parse_flat_json(raw);

    tgp::EstimateInput input;
    auto get = [&](const std::string& key) -> std::string {
        auto it = fields.find(key);
        return it == fields.end() ? std::string() : it->second;
    };
    auto get_double = [&](const std::string& key) -> double {
        const std::string v = get(key);
        try { return v.empty() ? 0.0 : std::stod(v); } catch (...) { return 0.0; }
    };
    auto get_int = [&](const std::string& key) -> int {
        const std::string v = get(key);
        try { return v.empty() ? 0 : std::stoi(v); } catch (...) { return 0; }
    };

    input.construction_type = get("construction_type");
    input.land_area_m2 = get_double("land_area_m2");
    input.footprint_area_m2 = get_double("footprint_area_m2");
    input.floors = get_int("floors");
    input.foundation_type = get("foundation_type");
    input.roof_type = get("roof_type");
    input.finish_level = get("finish_level");
    input.location = get("location");

    const tgp::EstimateResult r = tgp::compute_estimate(input);

    std::ostringstream out;
    out << std::fixed;
    out << "{";
    out << "\"valid\":" << (r.valid ? "true" : "false") << ",";
    if (!r.valid) {
        out << "\"error_message\":\"" << json_escape(r.error_message) << "\"";
        out << "}";
        std::cout << out.str() << std::endl;
        return 1;
    }
    out << std::setprecision(2);
    out << "\"footprint_area_m2\":" << r.footprint_area_m2 << ",";
    out << "\"foundation_coefficient\":" << r.foundation_coefficient << ",";
    out << "\"roof_coefficient\":" << r.roof_coefficient << ",";
    out << "\"total_construction_area_m2\":" << r.total_construction_area_m2 << ",";
    out << std::setprecision(0);
    out << "\"unit_price_vnd_per_m2\":" << r.unit_price_vnd_per_m2 << ",";
    out << std::setprecision(2);
    out << "\"location_multiplier\":" << r.location_multiplier << ",";
    out << "\"type_multiplier\":" << r.type_multiplier << ",";
    out << std::setprecision(0);
    out << "\"estimated_cost_vnd\":" << r.estimated_cost_vnd << ",";
    out << "\"cost_range_min_vnd\":" << r.cost_range_min_vnd << ",";
    out << "\"cost_range_max_vnd\":" << r.cost_range_max_vnd;
    out << "}";

    std::cout << out.str() << std::endl;
    return 0;
}
