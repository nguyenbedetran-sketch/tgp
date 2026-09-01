"""Construction cost estimate tool.

POST /api/estimate validates the form input, delegates the actual
calculation to the compiled C++ engine (app/services/cpp_bridge.py) and
logs every request to the `estimates` table for later analysis.
"""
import json
import logging

from flask import Blueprint, request

from app.models.db import get_db
from app.services.cpp_bridge import CppBridgeError, run_estimate
from app.utils.rate_limit import rate_limited
from app.utils.responses import err, ok
from app.utils.validation import as_float, as_int, clamp_str, require

logger = logging.getLogger("tgp.estimate")

bp = Blueprint("estimate", __name__, url_prefix="/api/estimate")

VALID_TYPES = {"nha_pho", "biet_thu", "van_phong", "nha_xuong", "cai_tao"}
VALID_FOUNDATIONS = {"don", "bang", "be", "coc"}
VALID_ROOFS = {"bang", "thai_nhat", "ton"}
VALID_FINISH = {"tho", "co_ban", "trung_binh", "cao_cap"}

DISCLAIMER = (
    "Kết quả chỉ mang tính chất tham khảo. Chi phí thực tế phụ thuộc vào hồ sơ "
    "thiết kế, vật liệu, vị trí và điều kiện thi công. Đây không phải là báo giá "
    "chính thức từ Trần Gia Phát."
)


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "")


@bp.post("")
@rate_limited()
def estimate():
    data = request.get_json(silent=True) or {}

    try:
        require(data, ["construction_type", "footprint_area_m2", "floors", "foundation_type",
                        "roof_type", "finish_level"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))

    if data["construction_type"] not in VALID_TYPES:
        return err(f"construction_type không hợp lệ. Cho phép: {sorted(VALID_TYPES)}", 422)
    if data["foundation_type"] not in VALID_FOUNDATIONS:
        return err(f"foundation_type không hợp lệ. Cho phép: {sorted(VALID_FOUNDATIONS)}", 422)
    if data["roof_type"] not in VALID_ROOFS:
        return err(f"roof_type không hợp lệ. Cho phép: {sorted(VALID_ROOFS)}", 422)
    if data["finish_level"] not in VALID_FINISH:
        return err(f"finish_level không hợp lệ. Cho phép: {sorted(VALID_FINISH)}", 422)

    footprint = as_float(data.get("footprint_area_m2"))
    floors = as_int(data.get("floors"))
    if footprint <= 0:
        return err("Diện tích xây dựng phải lớn hơn 0", 422)
    if floors <= 0 or floors > 20:
        return err("Số tầng không hợp lệ", 422)

    payload = {
        "construction_type": data["construction_type"],
        "land_area_m2": as_float(data.get("land_area_m2")),
        "footprint_area_m2": footprint,
        "floors": floors,
        "foundation_type": data["foundation_type"],
        "roof_type": data["roof_type"],
        "finish_level": data["finish_level"],
        "location": clamp_str(data.get("location"), 200),
    }

    try:
        result = run_estimate(payload)
    except CppBridgeError as exc:
        logger.error("Estimate calculation failed: %s", exc)
        return err(str(exc), 502)

    db = get_db()
    db.execute(
        """INSERT INTO estimates (contact_name, phone, input_json, result_json, ip_address)
           VALUES (?, ?, ?, ?, ?)""",
        (
            clamp_str(data.get("contact_name"), 150), clamp_str(data.get("phone"), 30),
            json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False),
            _client_ip(),
        ),
    )
    db.commit()

    return ok({
        "footprint_area_m2": result["footprint_area_m2"],
        "total_construction_area_m2": result["total_construction_area_m2"],
        "unit_price_vnd_per_m2": result["unit_price_vnd_per_m2"],
        "estimated_cost_vnd": result["estimated_cost_vnd"],
        "cost_range_min_vnd": result["cost_range_min_vnd"],
        "cost_range_max_vnd": result["cost_range_max_vnd"],
        "disclaimer": DISCLAIMER,
    })
