// calculator.cpp
// Tran Gia Phat - Construction cost estimation engine (C++)
//
// Implements the formulas used by the "Uoc tinh chi phi xay dung" tool.
// The coefficients and unit prices below are common, publicly known rules of
// thumb used across the Vietnamese residential construction industry for
// *preliminary* estimation (not an official price list of any company).
// They are clearly surfaced back to the user together with a disclaimer by
// the Python API layer, per project requirements ("khong duoc coi ket qua
// la bao gia chinh thuc").

#include "calculator.h"

#include <algorithm>
#include <cctype>
#include <vector>

namespace tgp {

namespace {

std::string to_lower(const std::string& s) {
    std::string out = s;
    std::transform(out.begin(), out.end(), out.begin(),
                    [](unsigned char c) { return std::tolower(c); });
    return out;
}

// Foundation coefficient: extra % of footprint area billed for the
// foundation works, depending on foundation type.
double foundation_coefficient(const std::string& raw) {
    const std::string t = to_lower(raw);
    if (t == "don") return 0.05;      // mong don
    if (t == "bang") return 0.30;     // mong bang
    if (t == "be") return 0.50;       // mong be
    if (t == "coc") return 0.40;      // mong coc / dai coc
    return 0.20;                      // default / unknown
}

// Roof coefficient: extra % of footprint area billed for the roof works.
double roof_coefficient(const std::string& raw) {
    const std::string t = to_lower(raw);
    if (t == "bang") return 0.30;        // mai bang (san thuong)
    if (t == "thai_nhat") return 0.60;   // mai thai / mai nhat (mai ngoi doc)
    if (t == "ton") return 0.15;         // mai ton
    return 0.30;
}

// Base unit price (VND / m2) by finish level. These are indicative,
// mid-market figures for reference only.
double base_unit_price(const std::string& raw) {
    const std::string t = to_lower(raw);
    if (t == "tho") return 3500000.0;
    if (t == "co_ban") return 4800000.0;
    if (t == "trung_binh") return 5800000.0;
    if (t == "cao_cap") return 7500000.0;
    return 4800000.0;
}

double type_multiplier(const std::string& raw) {
    const std::string t = to_lower(raw);
    if (t == "nha_pho") return 1.00;
    if (t == "biet_thu") return 1.15;
    if (t == "van_phong") return 1.10;
    if (t == "nha_xuong") return 0.85;
    if (t == "cai_tao") return 0.60;
    return 1.00;
}

// Small regional multiplier based on free-text location. This is a rough
// heuristic (materials/labour tend to cost slightly more in major cities)
// and is intentionally conservative.
double location_multiplier(const std::string& raw) {
    const std::string t = to_lower(raw);
    const std::vector<std::string> big_cities = {
        "ha noi", "hà nội", "tp hcm", "tp.hcm", "ho chi minh", "hồ chí minh",
        "da nang", "đà nẵng", "sai gon", "sài gòn"};
    for (const auto& city : big_cities) {
        if (t.find(city) != std::string::npos) return 1.05;
    }
    if (t.empty()) return 1.00;
    return 1.00;
}

}  // namespace

EstimateResult compute_estimate(const EstimateInput& input) {
    EstimateResult r;

    if (input.footprint_area_m2 <= 0.0) {
        r.valid = false;
        r.error_message = "Diện tích xây dựng (footprint_area_m2) phải lớn hơn 0";
        return r;
    }
    if (input.floors <= 0) {
        r.valid = false;
        r.error_message = "Số tầng (floors) phải lớn hơn 0";
        return r;
    }

    r.footprint_area_m2 = input.footprint_area_m2;
    r.foundation_coefficient = foundation_coefficient(input.foundation_type);
    r.roof_coefficient = roof_coefficient(input.roof_type);

    // Total billable construction area:
    //   (footprint * so_tang)                -> floor slabs
    // + (footprint * foundation_coefficient)  -> foundation works
    // + (footprint * roof_coefficient)        -> roof works
    const double floors_area = input.footprint_area_m2 * static_cast<double>(input.floors);
    const double foundation_area = input.footprint_area_m2 * r.foundation_coefficient;
    const double roof_area = input.footprint_area_m2 * r.roof_coefficient;

    r.total_construction_area_m2 = floors_area + foundation_area + roof_area;

    r.unit_price_vnd_per_m2 = base_unit_price(input.finish_level);
    r.location_multiplier = location_multiplier(input.location);
    r.type_multiplier = type_multiplier(input.construction_type);

    r.estimated_cost_vnd = r.total_construction_area_m2 * r.unit_price_vnd_per_m2 *
                            r.location_multiplier * r.type_multiplier;

    // Realistic estimation range: actual cost typically varies -10% / +15%
    // depending on the final design brief, material choices and site
    // conditions.
    r.cost_range_min_vnd = r.estimated_cost_vnd * 0.90;
    r.cost_range_max_vnd = r.estimated_cost_vnd * 1.15;

    r.valid = true;
    return r;
}

}  // namespace tgp
