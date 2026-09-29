"""
Basic colour/quality analysis of a leaf photo. This is deliberately NOT
presented as a trained image classifier — it is HSV colour-bucket analysis
plus a simple sharpness/brightness check, and it only ever produces weak
*hints* that get combined with the farmer's answers in reasoning.py. A real
CNN trained on labelled leaf photos (PlantVillage/PlantDoc) is future work
once that dataset is in hand — see docs/architecture.md phase 6.
"""
import io

import numpy as np
from PIL import Image


def _grayscale_sharpness(gray: np.ndarray) -> float:
    """Variance of a simple discrete Laplacian — higher = sharper. Not a
    calibrated focus-measure algorithm, just enough to flag an obviously
    blurry photo."""
    lap = (
        -4 * gray[1:-1, 1:-1]
        + gray[:-2, 1:-1] + gray[2:, 1:-1]
        + gray[1:-1, :-2] + gray[1:-1, 2:]
    )
    return float(np.var(lap))


def analyze_image(image_bytes: bytes) -> dict:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return {"error": f"could not read image: {e}"}

    img.thumbnail((512, 512))
    arr = np.asarray(img).astype(np.float32)
    gray = arr.mean(axis=2)

    hsv = np.asarray(img.convert("HSV")).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    total = h.size

    # PIL hue is 0-255 for a 0-360 degree wheel
    def frac(mask):
        return round(float(mask.sum()) / total, 4)

    green_pct = frac((h >= 60) & (h <= 120) & (s > 40))
    yellow_pct = frac((h >= 30) & (h < 60) & (s > 40))
    brown_pct = frac((h >= 10) & (h < 30) & (s > 60) & (v < 150))
    dark_spot_pct = frac((v < 70) & (s > 20))
    purple_pct = frac((h >= 200) & (h <= 260) & (s > 40))
    white_powdery_pct = frac((s < 40) & (v > 170))

    sharpness = _grayscale_sharpness(gray)
    brightness = float(gray.mean())

    warnings = []
    if sharpness < 50:
        warnings.append("Photo looks blurry — retake it holding the phone steady, closer to the leaf.")
    if brightness < 50:
        warnings.append("Photo looks too dark — retake it in better light.")
    elif brightness > 220:
        warnings.append("Photo looks overexposed — avoid direct harsh sunlight/flash on the leaf.")

    # Weak hints only, not conclusions — reasoning.py combines these with
    # the farmer's follow-up answers.
    photo_hints = {}
    if white_powdery_pct > 0.08:
        photo_hints["white_powdery_coating"] = min(1.0, white_powdery_pct * 4)
    if dark_spot_pct > 0.05:
        photo_hints["brown_spots_with_halo"] = min(1.0, dark_spot_pct * 3)
    if purple_pct > 0.05:
        photo_hints["purple_leaf_veins"] = min(1.0, purple_pct * 4)

    return {
        "color_breakdown": {
            "green_pct": green_pct, "yellow_pct": yellow_pct, "brown_pct": brown_pct,
            "dark_spot_pct": dark_spot_pct, "purple_pct": purple_pct, "white_powdery_pct": white_powdery_pct,
        },
        "yellow_fraction": yellow_pct,  # generic hint — which cause it points to needs a follow-up question
        "photo_hints": photo_hints,
        "quality_warnings": warnings,
        "sharpness_score": round(sharpness, 1),
        "brightness": round(brightness, 1),
    }
