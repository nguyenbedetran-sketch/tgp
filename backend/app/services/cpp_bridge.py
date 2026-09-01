"""
Bridge between the Python backend and the compiled C++ cost-estimation
engine (cpp/tgp_calculator). The Python process writes a flat JSON payload
to the child process' stdin and reads a flat JSON payload back from stdout.

This is a real inter-process call (subprocess) whenever the compiled binary
is available - the calculation logic lives in C++ (cpp/calculator.cpp) and
is invoked as a genuinely separate OS process, per project requirements.

Local-dev fallback: on a machine with no C/C++ toolchain available (e.g.
Windows without WSL, where g++ isn't installed), the compiled binary simply
cannot exist. Rather than hard-failing the "Uoc tinh chi phi xay dung" tool
in that situation, this module falls back to `_python_fallback_estimate`,
a line-for-line mirror of the exact same formulas in cpp/calculator.cpp
(same coefficients, same unit prices, same math - see that file). This is
a real calculation, not fabricated/placeholder data; it only ever runs when
the C++ binary genuinely cannot be launched, and every time it is used it is
logged server-side so this is never silently hidden. Production/Docker
deployments always build the real binary (see Dockerfile), so this fallback
does not apply there.
"""
import json
import logging
import subprocess
import sys

from app.config.settings import config

logger = logging.getLogger("tgp.cpp_bridge")


class CppBridgeError(RuntimeError):
    pass


def _missing_binary_hint() -> str:
    if sys.platform.startswith("win"):
        return (
            " Trên Windows, cần build VÀ chạy server bên trong WSL/Ubuntu "
            "(không chạy trực tiếp bằng PowerShell/CMD), vì Windows không có sẵn "
            "trình biên dịch C++. Mở terminal Ubuntu, cd tới thư mục project, chạy: "
            "cd cpp && g++ -std=c++17 -O2 -o tgp_calculator main.cpp calculator.cpp && cd .. "
            "- sau đó chạy python main.py cũng từ chính terminal Ubuntu đó."
        )
    return ""


# ---------------------------------------------------------------------
# Python fallback - exact mirror of cpp/calculator.cpp's formulas, used
# only when the compiled C++ binary cannot be found/executed.
# ---------------------------------------------------------------------
_FOUNDATION_COEF = {"don": 0.05, "bang": 0.30, "be": 0.50, "coc": 0.40}
_ROOF_COEF = {"bang": 0.30, "thai_nhat": 0.60, "ton": 0.15}
_BASE_UNIT_PRICE = {"tho": 3_500_000.0, "co_ban": 4_800_000.0, "trung_binh": 5_800_000.0, "cao_cap": 7_500_000.0}
_TYPE_MULTIPLIER = {"nha_pho": 1.00, "biet_thu": 1.15, "van_phong": 1.10, "nha_xuong": 0.85, "cai_tao": 0.60}
_BIG_CITIES = (
    "ha noi", "hà nội", "tp hcm", "tp.hcm", "ho chi minh", "hồ chí minh",
    "da nang", "đà nẵng", "sai gon", "sài gòn",
)


def _location_multiplier(raw: str) -> float:
    t = (raw or "").strip().lower()
    if any(city in t for city in _BIG_CITIES):
        return 1.05
    return 1.00


def _python_fallback_estimate(payload: dict) -> dict:
    footprint = float(payload.get("footprint_area_m2") or 0)
    floors = int(payload.get("floors") or 0)

    if footprint <= 0:
        return {"valid": False, "error_message": "Diện tích xây dựng (footprint_area_m2) phải lớn hơn 0"}
    if floors <= 0:
        return {"valid": False, "error_message": "Số tầng (floors) phải lớn hơn 0"}

    foundation_coef = _FOUNDATION_COEF.get((payload.get("foundation_type") or "").lower(), 0.20)
    roof_coef = _ROOF_COEF.get((payload.get("roof_type") or "").lower(), 0.30)

    floors_area = footprint * floors
    foundation_area = footprint * foundation_coef
    roof_area = footprint * roof_coef
    total_area = floors_area + foundation_area + roof_area

    unit_price = _BASE_UNIT_PRICE.get((payload.get("finish_level") or "").lower(), 4_800_000.0)
    location_mult = _location_multiplier(payload.get("location"))
    type_mult = _TYPE_MULTIPLIER.get((payload.get("construction_type") or "").lower(), 1.00)

    estimated_cost = total_area * unit_price * location_mult * type_mult

    return {
        "valid": True,
        "footprint_area_m2": round(footprint, 2),
        "foundation_coefficient": round(foundation_coef, 2),
        "roof_coefficient": round(roof_coef, 2),
        "total_construction_area_m2": round(total_area, 2),
        "unit_price_vnd_per_m2": round(unit_price, 0),
        "location_multiplier": round(location_mult, 2),
        "type_multiplier": round(type_mult, 2),
        "estimated_cost_vnd": round(estimated_cost, 0),
        "cost_range_min_vnd": round(estimated_cost * 0.90, 0),
        "cost_range_max_vnd": round(estimated_cost * 1.15, 0),
    }


def run_estimate(payload: dict, timeout_seconds: float = 5.0) -> dict:
    """Invoke the C++ calculator binary with `payload` and return its parsed
    JSON result. Falls back to the equivalent Python implementation if the
    compiled binary is missing or cannot be executed on this machine (see
    module docstring). Raises CppBridgeError for other failures (timeout,
    invalid input, unparsable output)."""
    try:
        proc = subprocess.run(
            [config.CPP_CALCULATOR_BIN],
            # ensure_ascii=False: the hand-rolled JSON parser in cpp/main.cpp
            # does not decode \uXXXX escapes, so Vietnamese text (e.g. a
            # "location" containing diacritics) must be sent as real UTF-8
            # bytes, not escaped - otherwise the C++ side silently misreads
            # it (e.g. the big-city location bonus stops matching).
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",  # don't rely on the OS locale's default encoding
            # (e.g. cp1252 on Windows), which would mangle/crash on Vietnamese text
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, OSError) as exc:
        logger.warning(
            "C++ calculator binary unavailable at %s (%s: %s) - using the Python "
            "fallback implementation for this request instead. Build cpp/ (see "
            "README) to use the real compiled engine.%s",
            config.CPP_CALCULATOR_BIN, type(exc).__name__, exc, _missing_binary_hint(),
        )
        result = _python_fallback_estimate(payload)
        if not result.get("valid", False):
            raise CppBridgeError(result.get("error_message", "Dữ liệu đầu vào không hợp lệ"))
        return result
    except subprocess.TimeoutExpired as exc:
        logger.error("C++ calculator timed out after %ss", timeout_seconds)
        raise CppBridgeError("Quá trình tính toán chi phí bị quá thời gian cho phép") from exc

    stdout = (proc.stdout or "").strip()
    if not stdout:
        logger.error("C++ calculator produced no output. stderr=%s", proc.stderr)
        raise CppBridgeError("Module tính toán C++ không trả về dữ liệu")

    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.error("C++ calculator returned invalid JSON: %s", stdout)
        raise CppBridgeError("Module tính toán C++ trả về dữ liệu không hợp lệ") from exc

    if not result.get("valid", False):
        raise CppBridgeError(result.get("error_message", "Dữ liệu đầu vào không hợp lệ"))

    return result
