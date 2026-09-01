// calculator.h
// Tran Gia Phat - Construction cost estimation engine (C++)
//
// This header exposes a small, dependency-free calculation engine used to
// estimate construction area and construction cost for a given project.
// The engine is intentionally kept as pure C++ (no external libraries) so it
// can be compiled anywhere with a standard C++17 compiler and does not
// require network access or third-party JSON libraries.
//
// The Python backend talks to this module as a separate OS process (see
// main.cpp): it writes a single-line flat JSON object to the process' stdin
// and reads a single-line flat JSON object back from stdout. This keeps the
// C++ module a genuinely independent, testable service instead of a
// decorative dependency.

#pragma once

#include <string>

namespace tgp {

// Raw inputs coming from the "Ước tính chi phí xây dựng" form on the website.
struct EstimateInput {
    std::string construction_type;   // "nha_pho" | "biet_thu" | "van_phong" | "nha_xuong" | "cai_tao"
    double land_area_m2 = 0.0;       // Dien tich dat (m2)
    double footprint_area_m2 = 0.0;  // Dien tich xay dung / san mot tang (m2)
    int floors = 1;                  // So tang
    std::string foundation_type;     // "don" | "bang" | "be" | "coc"
    std::string roof_type;           // "bang" | "thai_nhat" | "ton"
    std::string finish_level;        // "tho" | "co_ban" | "trung_binh" | "cao_cap"
    std::string location;            // free text location, used for a small regional multiplier
};

// Computed results returned to the caller.
struct EstimateResult {
    double footprint_area_m2 = 0.0;
    double foundation_coefficient = 0.0;   // fraction of footprint added for foundation works
    double roof_coefficient = 0.0;         // fraction of footprint added for roof works
    double total_construction_area_m2 = 0.0; // "dien tich xay dung tinh phi"
    double unit_price_vnd_per_m2 = 0.0;
    double location_multiplier = 1.0;
    double type_multiplier = 1.0;
    double estimated_cost_vnd = 0.0;
    double cost_range_min_vnd = 0.0;
    double cost_range_max_vnd = 0.0;
    bool valid = true;
    std::string error_message;
};

// Core calculation entry point. Pure function, no I/O, fully unit-testable.
EstimateResult compute_estimate(const EstimateInput& input);

}  // namespace tgp
