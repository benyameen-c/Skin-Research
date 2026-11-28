#!/usr/bin/env python3
"""Re-run the quote check for content/external/gemini-instrument-repeatability-2026-11-28.md.

Source texts are not committed. Copy them from the project files folder
papers/excerpts/ into papers/excerpts/ first, or pass that folder as the argument:

  python3 tools/instrument_report_check.py /mnt/project-files/papers/excerpts

A quote passes if it appears after Unicode and whitespace normalisation
(EXACT/NORM), or after also ignoring case and punctuation (LOOSE: used only for
"RESULTS:" capitals and table-cell bullets, noted in the write-up).
Kanellis 2019 (R21) is expected to FAIL: its full text is not open.
"""
import re, sys, unicodedata
from pathlib import Path

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "papers" / "excerpts"

# (id, source files, quote). R = quoted in the report; A = quoted in the appendices.
Q = [
("R1", "pmc_7478811.txt", "Moreover, good correlations were observed for all the parameters analyzed, and the Antera 3D had a higher repeatability."),
("R2", "pmc_11252344.txt", "Measurement area: 56 mm × 56 mm"),
("R3", "pmc_6547281.txt", "Achromic laser tattoo scars. a, b Images using the Antera 3D® colorimetry system at baseline (a), and after three MMP® sessions with 5-FU (b). The areas outlined in black correspond to where we assessed melanin levels using the Antera 3D® software (c)."),
("R4", "pmid_18388577.txt", "The ICC for the Mexameter erythema (>0.75) and melanin index (>0.89) and the DermaScan C total thickness measurement (>0.82) were acceptable for all sites."),
("R5", "pmc_9299221.txt", "The Mexameter MX 18 and DSM II ColorMeter achieved good interobserver reliability (ICC 0.92–0.94 and 0.89–0.96, respectively)."),
("R6", "pmc_9299221.txt", "Intraobserver reliability was not tested for the Mexameter MX 18, DSM II ColorMeter, ColoriMeter CL‐400, and DermaLab Combo."),
("R7", "pmc_11252344.txt", "Measurement surface: 5 mm ≈ 19.6 mm²"),
("R8", "pmc_11727858.txt", "In this study, the analyzed skin area was approximately 19.6 mm2 (disc diameter of approximately 5 mm) and was analyzed once"),
("R9", "pmid_17026663.txt", "A selection of 202 hypopigmented skin lesions (182 from vitiligo and 20 from ND) were the objects of this study. Using a Mexameter, MIs were obtained from lesions and symmetrically located control skin."),
("R10", "pmid_17026663.txt", "The mean RMI of ND lesions was 74+/-13, which was significantly higher than that of vitiligo lesions (50+/-24)."),
("R11", "pmid_21165227.txt", "Improvements in the two lesions were assessed with clinical photography and using a Mexameter® (Courage-Khazaka Electronic, Germany), which is a pigment-measuring device."),
("R12", "pmid_29057565.txt", "Results: MX18 and CM-700d can quantitatively distinguish vitiligo/leukoderma from normally pigmented skin based on melanin index."),
("R13", "pmid_29057565.txt", "Japan Tissue Engineering Co., Ltd., Gamagori, Aichi, Japan"),
("R14", "pmid_11301642.txt", "Results: Results showed excellent values for ICC in all the four conditions."),
("R15", "pmc_9299221.txt", "Interobserver reliability was highest for the Minolta Chromameter CR‐300 (Table 5). Van den Kerckhove et al. reported intraclass coefficients between 0.92 and 0.99 in 60 patients with measurements provided by two independent observers."),
("R16", "pmc_9299221.txt", "Both Van den Kerckhove et al. and Uter et al. reported good intraobserver reliability for the Minolta Chromameter as well (ICC 0.98–0.99 and 0.926–0.954,"),
("R17", "pmc_11252344.txt", "Measurement surface: 8 mm"),
("R18", "pmc_6731390.txt", "In terms of pigmentation measurement, the DSM II L*, and narrow band Melanin parameters both show high inter- and intra-rater ICC values of above 0.90 for both"),
("R19", "pmc_11888493.txt", "Among subjects with repeat skin measurements over time, objective assessment provided consistent measures with a mean range of ITA across study days of 11.9° (95% CI: 10.8° - 12.9°)."),
("R20", "pmc_11252344.txt", "Measurement surface: 8 mm and 3 mm"),
("R21", "pmc_6874939.txt", "CM-2600d (Konica Minolta, Japan) Remittance spectroscopy at 390 nm at a 15-nm bandwidth with an 8-mm aperture."),
("R22", "pmid_29057565.txt", "ΔE*ab seems to be a useful parameter to evaluate the color contrast between vitiligo/leukoderma and surrounding normally pigmented skin and can be used to evaluate disease severity and patient's quality of life."),
("R23", "pmc_2850874.txt", "The reproducibility, visualized by the probability distribution of the dE_ab errors between 2 measurements of the patches of the images has a median of 3.43 dE* for all calibrated images, 23.26 dE_ab for all uncalibrated images. If we restrict ourselves to the proper patches of normal calibrated images the median is only 2.58 dE_ab!"),
("R24", "pmc_2850874.txt", "Colour differences between the measurements and real spectrophotometric measurements reveal median dE_ab values respectively 6.40 for the proper patches of calibrated normal images and 17.75 for uncalibrated images demonstrating an important improvement in accuracy after calibration."),
("R25", "pmc_3778111.txt", "Results of ICCs for intra-rater agreement showed high levels of internal consistency reliability within each rater for the lasso technique (ICC ≥ 0.99) and somewhat lower, yet acceptable, level of agreement for the color sampler technique (ICC = 0.91 for expert, ICC = 0.81 for novice). Skin L*, skin b*, and labia L* values reached the highest level of agreement (ICC ≥ 0.92) and skin a*, labia b*, and vaginal wall b* were the lowest (ICC ≥ 0.64)."),
("A1a", "pmc_7478811.txt", "Ana et al[16] compared the Antera 3D"),
("A1b", "pmc_9299221.txt", "However, one of these studies was performed by a contract research organization, which developed the investigated device. 15"),
("A1c", "pmc_9299221.txt", "Skin colour, skin redness and melanin biometric measurements: comparison study between Antera((R)) 3D, Mexameter((R)) and Colorimeter((R))"),
("A2", "pmid_23237819.txt", "All three instruments provided reliable readings (intraclass correlation coefficient ≥ 0.83; confidence interval: 0.71-0.90) on normal skin and scar tissue."),
("A2b", "pmid_23237819.txt", "Fifty scars"),
("A3a", "pmid_11301642.txt", "healthy skin of 30 volunteers"),
("A3b", "pmid_11301642.txt", "repeated measurements with a 1 week time lapse"),
("A3c", "pmc_9299221.txt", "Kerckhove et al., 2001 | Minolta Chromameter CR‐300 | 0.98–0.99 | 0.92–0.99 | 0.99–0.999"),
("A5a", "pmc_6731390.txt", "above 0.90 for both single and average measures"),
("A5b", "pmc_6731390.txt", "The inter-and intra-rater for the L* value for normal skin, although lower, were also all above the set threshold of 0.70 (ICC Single or Average = 0.806–0.960)."),
("A5c", "pmc_6731390.txt", "3 different assessors 3 times over a period of one day"),
("A6", "pmc_6731390.txt", "has a skin measuring area of 4 mm in diameter"),
("A7a", "pmc_11239860.txt", "ICCs > 0.90 were considered to indicate excellent reliability"),
("A7b", "pmc_11239860.txt", "excellent results (ICC > 0.90 and/or |CV | < 10%) were obtained in approximately 85%, 75%, and 67% of intra-observer, inter-observer, and inter-instrument studies, respectively."),
("A8a", "pmc_2850874.txt", "MacBeth Colour Checker Chart Mini"),
("A8b", "pmc_2850874.txt", "Median of 3.43 dE*ab for all calibrated image"),
("A8c", "pmc_2850874.txt", "based on 39 images taken with a Nikon D200 and 15 images with a Canon 10D under different illuminants and settings"),
("A8d", "pmc_2850874.txt", "All images were processed in high-quality jpeg mode."),
("A9a", "pmc_11888493.txt", "The DSCC and VL were only used in the ICU cohort."),
("A9b", "pmc_11888493.txt", "Assessment of triplicate measurements at the forehead for the same participant showed a mean ΔITA of 0.8 ± 1.6 and ΔE 0.6 ± 0.6 for the KM-700d, and ΔITA 1.0 ± 1.8 and ΔE 1.4 ± 1.0 for the DSCC."),
("A10", "pmid_11428962.txt", "The in vitro and in vivo repeatabilty as well as the sensitivity of the three instruments are rather good."),
("A11a", "pmc_7478811.txt", "This work was supported by a grant from the National Natural Science Foundation of China"),
("A11b", "pmc_9299221.txt", "The authors received no specific funding for this work."),
("A11c", "pmc_11727858.txt", "The authors declare no conflicts of interest."),
("A11d", "pmc_6731390.txt", "This work was supported by The Scar Free Foundation"),
("A11e", "pmc_11888493.txt", "No company provided any direct funding for this study"),
("A11f", "pmc_2850874.txt", "The authors declare that they have no competing interests."),
("A11g", "pmc_11239860.txt", "The authors declare no competing interests."),
("A11h", "pmc_6547281.txt", "The first author is the owner of Traderm"),
("A11i", "pmc_6547281.txt", "The tattooing machine, cartridges, and drug used in this study were supplied by Traderm"),
("A11j", "pmc_3778111.txt", "US National Institutes of Health"),
("A12", "pmid_29057565.txt", "rhododendrol"),
("P2a", "pmc_6731390.txt", "8.10 (1.63)"),
("P2b", "pmc_6731390.txt", "5.20 (1.03)"),
("P2c", "pmc_6731390.txt", "Mean27.07 6.61 46.36 37.67"),
("P2d", "pmc_6731390.txt", "37.75–43.34"),
("P2e", "pmc_6731390.txt", "Standard Error of Mean (SEM)"),
("P5", "pmid_17026663.txt", "50+/-24"),
]


def norm(s, loose=False):
    s = unicodedata.normalize("NFKC", s)
    for a, b in [("‐", "-"), ("‑", "-"), ("–", "-"), ("—", "-"), ("−", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')]:
        s = s.replace(a, b)
    s = " ".join(s.split())
    if loose:
        s = re.sub(r"[^a-z0-9]", "", s.lower())
    return s


def main():
    fails = 0
    for qid, fname, quote in Q:
        path = SRC / fname
        if not path.exists():
            print(f"{qid}\tMISSING\t{fname}"); fails += 1; continue
        text = path.read_text(encoding="utf-8")
        if norm(quote) in norm(text):
            res = "OK"
        elif norm(quote, True) in norm(text, True):
            res = "OK-LOOSE"
        else:
            res = "FAIL"; fails += 1
        print(f"{qid}\t{res}\t{fname}")
    print(f"{len(Q)} quotes, {fails} not found")


if __name__ == "__main__":
    main()
