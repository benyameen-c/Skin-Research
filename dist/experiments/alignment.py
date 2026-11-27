from math import acos, pi, sqrt

def contrast_retained(diameter_mm, shift_mm):
    """Fraction of a uniform spot inside an equally sized, displaced mask."""
    if diameter_mm <= 0 or shift_mm < 0:
        raise ValueError("Use a positive diameter and a nonnegative displacement")
    separation = shift_mm / diameter_mm
    if separation >= 1:
        return 0.0
    return 2 * (acos(separation) - separation * sqrt(1 - separation**2)) / pi

assert contrast_retained(2, 0) == 1.0
assert contrast_retained(2, 2) == 0.0
assert contrast_retained(2, 0.25) < contrast_retained(5, 0.25)
print("diameter_mm,shift_mm,false_contrast_reduction_pct")
for diameter in (2, 3, 5):
    for shift in (0, 0.25, 0.5):
        false_change = 100 * (1 - contrast_retained(diameter, shift))
        print(f"{diameter},{shift},{false_change:.1f}")
