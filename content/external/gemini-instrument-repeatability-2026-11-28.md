# External report: repeatability of skin colour instruments (Google Gemini)

**Origin.** Written by Google Gemini from a copy-paste prompt the project gave Ben (prompt 13: repeatability of skin colour instruments, smallest lesion size tested, use on white or hypopigmented spots, manufacturer funding). Ben pasted it into the project thread on 2026-11-28 at 13:21 UTC.

**Status: UNVERIFIED LEADS.** Nothing below has entered `data/evidence.csv`, and nothing from these papers is to be extracted into the ledger. Under CLAUDE.md rule 9, every claim here is a lead until a primary source is quoted. The quote check is Appendix 1, a check of the numbers and labels outside the quotes is Appendix 2, and Appendix 3 says how the checked figures bear on `content/measurement-tool-plan.md`. The appendices are the checking thread's work, not part of the report. The plan itself is not edited.

**Fidelity.** The report text between the two horizontal rules is as Ben pasted it, except that HTML entities introduced in transit (`&amp;`, `&gt;`, `&#34;`, `&#39;`, tab characters) are written as the characters they stand for, and the tab-separated summary table is set as a Markdown table with its cell text unchanged. Gemini's LaTeX fragments (`\Delta E`, `L^*`) are kept as received.

---

| Instrument / Method | Repeatability / Reproducibility (Retrieved Figures) | Smallest Lesion Size Tested (Device Aperture / FOV) | Used on White / Hypopigmented Spots | Manufacturer-Funded Flag |
|---|---|---|---|---|
| Antera 3D | Numeric SD/CV/ICC/\Delta E: not found (review notes higher repeatability than Mexameter/CL-400) | not found (imaging field: 56 mm × 56 mm) | Yes (achromic laser tattoo scars) | not found in retrieved excerpts |
| Mexameter (MX 16 / MX 18) | Intrarater ICC > 0.89 (melanin), > 0.75 (erythema); Interobserver ICC 0.92–0.94 (MX 18); SD/CV/\Delta E: not found | not found (probe aperture: 5 mm / ~19.6 mm²) | Yes (vitiligo, nevus depigmentosus, chemical leukoderma) | not found for reliability papers; Industry-affiliated co-authors in Hayashi et al. (2017) (Japan Tissue Engineering Co., Ltd.; not device maker) |
| Chromameter (Minolta CR-300 / CR-400; CL-400) | Minolta CR-300 interobserver ICC 0.92–0.99; intraobserver ICC 0.98–0.99 and 0.926–0.954; CL-400 & SD/CV/\Delta E: not found | not found (CR-400 aperture: 8 mm) | not found in retrieved validation excerpts | not found in retrieved excerpts |
| DSM Colorimeters (DSM II / III / 4) | DSM II interobserver ICC 0.89–0.96 (normal skin); inter- and intra-rater ICC > 0.90 for L^* and Melanin (scars/normal skin); DSM III/4 & SD/CV/\Delta E: not found | not found | not found for vitiligo/white spots (tested on burn scars & normal skin) | not found in retrieved excerpts |
| Spectrophotometers (CM-700d, CM-2600d, DermaSpectrometer) | CM-700d/objective repeat ITA mean range across study days: 11.9° (95% CI: 10.8°–12.9°); per-device SD/CV/ICC/\Delta E: not found | not found (CM-700d: 8 mm and 3 mm; CM-2600d: 8 mm) | Yes (CM-700d on vitiligo and chemical leukoderma) | not found for Lipnick et al. (2025); Industry-affiliated co-authors in Hayashi et al. (2017) (Japan Tissue Engineering Co., Ltd.; not Konica Minolta) |
| Calibrated Digital Photography (Color Chart) | Macbeth chart reproducibility median \Delta E^*_{ab} 3.43 (all) / 2.58 (proper patches) vs. 23.26 uncalibrated; Pictocolor chart intra-rater ICC ≥ 0.99 (lasso) / 0.81–0.91 (sampler), skin L^* & b^* ICC ≥ 0.92 | not found | not found directly in retrieved validation excerpts | not found in retrieved excerpts |

1. Antera 3D (Miravex)

⚬ Repeatability / Reproducibility: Numeric peer-reviewed values (SD, CV, ICC, or \Delta E) for skin color or pigmentation were not found in retrieved full-text excerpts. A melasma-imaging review summarizing comparison data against Mexameter and Colorimeter reports only a qualitative finding (Meng & Xu, 2020):
  "Moreover, good correlations were observed for all the parameters analyzed, and the Antera 3D had a higher repeatability." (DOI: 10.1097/cm9.0000000000000984)
⚬ Smallest Lesion Size Tested: not found. For reference, the camera's capture field is documented in a skin-tone assessment survey (Weir et al., 2024):
  "- Measurement area: 56 mm × 56 mm." (DOI: 10.1038/s41746-024-01176-8)
⚬ White / Hypopigmented Spots: Yes. Used longitudinally to quantify melanin recovery in achromic (depigmented) laser tattoo removal scars (Arbache et al., 2019):
  "Achromic laser tattoo scars. a, b Images using the Antera 3D® colorimetry system at baseline (a), and after three MMP® sessions with 5-FU (b). The areas outlined in black correspond to where we assessed melanin levels using the Antera 3D® software (c)." (DOI: 10.1159/000500709)
⚬ Manufacturer-Funded Flag: Funding disclosures were not found in the retrieved excerpts for Meng & Xu (2020), Weir et al. (2024), or Arbache et al. (2019).

2. Mexameter (Courage+Khazaka MX 16 / MX 18)

⚬ Repeatability / Reproducibility:
  ⚬ Intrarater reliability (hypertrophic burn scars and normal skin): Nedelec et al. (2008) reported intrarater ICCs across sites:
    "The ICC for the Mexameter erythema (>0.75) and melanin index (>0.89) and the DermaScan C total thickness measurement (>0.82) were acceptable for all sites." (PMID: 18388577; DOI: 10.1097/bcr.0b013e3181710869)
  ⚬ Interobserver reliability (ordinary skin, Mexameter MX 18): A systematic review by Langeveld et al. (2021) summarizing van der Wal et al. (2013) (PMID: 23237819; DOI: 10.1097/bcr.0b013e318264bf7d) reported:
    "The Mexameter MX 18 and DSM II ColorMeter achieved good interobserver reliability (ICC 0.92–0.94 and 0.89–0.96, respectively)." (DOI: 10.1111/srt.13113)
    "Intraobserver reliability was not tested for the Mexameter MX 18, DSM II ColorMeter, ColoriMeter CL‐400, and DermaLab Combo." (DOI: 10.1111/srt.13113)
  ⚬ SD, CV, or \Delta E: not found in retrieved excerpts (Clarys et al., 2000 [PMID: 11428962; DOI: 10.1034/j.1600-0846.2000.006004230.x] evaluated MX 16 in vitro and in vivo repeatability, but numeric table entries were not present in retrieved text).
⚬ Smallest Lesion Size Tested: not found. The fixed probe measurement surface imposes a physical ~5 mm circular sampling area:
  "Measurement surface: 5 mm ≈ 19.6 mm²" (Weir et al., 2024; DOI: 10.1038/s41746-024-01176-8)
  "In this study, the analyzed skin area was approximately 19.6 mm2 (disc diameter of approximately 5 mm) and was analyzed once" (Deda et al., 2024; DOI: 10.3390/jcm13247547)
⚬ White / Hypopigmented Spots: Yes. Applied to vitiligo, nevus depigmentosus (ND), and chemical leukoderma:
  "A selection of 202 hypopigmented skin lesions (182 from vitiligo and 20 from ND) were the objects of this study. Using a Mexameter, MIs were obtained from lesions and symmetrically located control skin." ... "The mean RMI of ND lesions was 74+/-13, which was significantly higher than that of vitiligo lesions (50+/-24)." (Park et al., 2006; PMID: 17026663; DOI: 10.1111/j.0909-752x.2006.00187.x)
  "Improvements in the two lesions were assessed with clinical photography and using a Mexameter® (Courage-Khazaka Electronic, Germany), which is a pigment-measuring device." (longitudinal tracking of coexistent vitiligo and nevus depigmentosus; Hwang et al., 2010; PMID: 21165227; DOI: 10.5021/ad.2010.22.4.482)
  "Results: MX18 and CM-700d can quantitatively distinguish vitiligo/leukoderma from normally pigmented skin based on melanin index." (Hayashi et al., 2017; PMID: 29057565; DOI: 10.1111/srt.12410)
⚬ Manufacturer-Funded Flag: Funding disclosures were not found in retrieved excerpts for Nedelec et al. (2008), van der Wal et al. (2013), Langeveld et al. (2021), Park et al. (2006), Hwang et al. (2010), or Deda et al. (2024). Flagged industry affiliation: Hayashi et al. (2017; PMID: 29057565; DOI: 10.1111/srt.12410) includes co-authors affiliated with "Japan Tissue Engineering Co., Ltd., Gamagori, Aichi, Japan" (an autologous tissue-engineering firm, not Courage+Khazaka).

3. Chromameter (Konica Minolta CR-200 / CR-300 / CR-400; Colorimeter CL-400)

⚬ Repeatability / Reproducibility:
  ⚬ Interobserver and intraobserver reliability (Minolta Chromameter CR-300, healthy skin): Kerckhove et al. (2001) reported "Results: Results showed excellent values for ICC in all the four conditions." (PMID: 11301642; DOI: 10.1034/j.1600-0846.2001.007001056.x). Exact numeric ICCs from Kerckhove et al. (2001) and Uter et al. were extracted in Langeveld et al. (2021):
    "Interobserver reliability was highest for the Minolta Chromameter CR‐300 (Table 5). Van den Kerckhove et al. reported intraclass coefficients between 0.92 and 0.99 in 60 patients with measurements provided by two independent observers." (DOI: 10.1111/srt.13113)
    "Both Van den Kerckhove et al. and Uter et al. reported good intraobserver reliability for the Minolta Chromameter as well (ICC 0.98–0.99 and 0.926–0.954," (DOI: 10.1111/srt.13113)
  ⚬ Colorimeter CL-400 and Chromameter SD, CV, or \Delta E: not found in retrieved excerpts (Clarys et al., 2000 [PMID: 11428962; DOI: 10.1034/j.1600-0846.2000.006004230.x] assessed CR-200 repeatability, but numeric table entries were not returned).
⚬ Smallest Lesion Size Tested: not found. The Konica Minolta CR-400 uses an 8 mm measurement surface (Weir et al., 2024):
  "- Measurement surface: 8 mm." (DOI: 10.1038/s41746-024-01176-8)
⚬ White / Hypopigmented Spots: not found in retrieved validation excerpts (retrieved studies tested healthy skin and burn scars).
⚬ Manufacturer-Funded Flag: Funding disclosures were not found in retrieved excerpts for Kerckhove et al. (2001), Clarys et al. (2000), van der Wal et al. (2013), or Langeveld et al. (2021).

4. DSM Colorimeters (Cortex Technology DSM II / DSM III / DSM 4 ColorMeter)

⚬ Repeatability / Reproducibility:
  ⚬ Interobserver reliability (DSM II ColorMeter, ordinary skin): Langeveld et al. (2021), reporting van der Wal et al. (2013) (PMID: 23237819; DOI: 10.1097/bcr.0b013e318264bf7d):
    "The Mexameter MX 18 and DSM II ColorMeter achieved good interobserver reliability (ICC 0.92–0.94 and 0.89–0.96, respectively)." (DOI: 10.1111/srt.13113)
  ⚬ Inter- and intra-rater reliability (DSM II ColorMeter, burn scars and normal skin): Lee et al. (2019):
    "In terms of pigmentation measurement, the DSM II L*, and narrow band Melanin parameters both show high inter- and intra-rater ICC values of above 0.90 for both" (DOI: 10.1016/j.burns.2019.02.002)
  ⚬ DSM III / DSM 4 numeric figures and DSM II SD, CV, or \Delta E: not found in retrieved excerpts (DSM III and DSM IV are listed in Vasudevan et al., 2024 [DOI: 10.1038/s43856-024-00550-7], without device-specific numeric reliability tables in retrieved snippets).
⚬ Smallest Lesion Size Tested: not found.
⚬ White / Hypopigmented Spots: not found for vitiligo or isolated hypopigmented macules in retrieved excerpts (retrieved studies evaluated burn scars and normal skin: van der Wal et al., 2013; Lee et al., 2019).
⚬ Manufacturer-Funded Flag: Funding disclosures were not found in retrieved excerpts for van der Wal et al. (2013), Lee et al. (2019), or Langeveld et al. (2021).

5. Spectrophotometers (Konica Minolta CM-700d, CM-2600d, DermaSpectrometer)

⚬ Repeatability / Reproducibility:
  ⚬ Longitudinal repeat measurements over study days (CM-700d / objective ICU skin-tone cohort): Lipnick et al. (2025; preprint) evaluated repeatability over time in hospitalized subjects using the Konica Minolta CM-700d and Delfin SkinColorCatch:
    "Among subjects with repeat skin measurements over time, objective assessment provided consistent measures with a mean range of ITA across study days of 11.9° (95% CI: 10.8° - 12.9°)." (PMID: 40061342; DOI: 10.1101/2025.02.21.25322707)
  ⚬ Per-instrument SD, CV, ICC, or \Delta E for CM-700d, CM-2600d, CM-2500d, or DermaSpectrometer: not found in retrieved excerpts. An FDA-led review of melanometers including Konica Minolta spectrophotometers (CM-600d, CM-700d, CM-2002) and narrowband devices summarized literature repeatability at the aggregate level as ICC greater than 0.90 and/or absolute CV less than 10% (Vasudevan et al., 2024; DOI: 10.1038/s43856-024-00550-7), but device-specific rows were not present in retrieved text.
⚬ Smallest Lesion Size Tested: not found. Reported instrument measurement apertures:
  ⚬ Konica Minolta CM-700d: "- Measurement surface: 8 mm and 3 mm." (Weir et al., 2024; DOI: 10.1038/s41746-024-01176-8)
  ⚬ Konica Minolta CM-2600d: "CM-2600d (Konica Minolta, Japan) Remittance spectroscopy at 390 nm at a 15-nm bandwidth with an 8-mm aperture." (Kanellis, 2019; DOI: 10.1007/s12551-019-00581-8)
⚬ White / Hypopigmented Spots: Yes. Konica Minolta CM-700d was evaluated on vitiligo and chemical leukoderma (Hayashi et al., 2017):
  "Results: MX18 and CM-700d can quantitatively distinguish vitiligo/leukoderma from normally pigmented skin based on melanin index." (PMID: 29057565; DOI: 10.1111/srt.12410)
  "ΔE*ab seems to be a useful parameter to evaluate the color contrast between vitiligo/leukoderma and surrounding normally pigmented skin and can be used to evaluate disease severity and patient's quality of life." (PMID: 29057565; DOI: 10.1111/srt.12410)
⚬ Manufacturer-Funded Flag: Funding disclosures were not found in retrieved excerpts for Lipnick et al. (2025), Vasudevan et al. (2024), Weir et al. (2024), Kanellis (2019), or Clarys et al. (2000). Flagged industry affiliation: Hayashi et al. (2017; PMID: 29057565; DOI: 10.1111/srt.12410) includes co-authors from "Japan Tissue Engineering Co., Ltd., Gamagori, Aichi, Japan" (not Konica Minolta).

6. Calibrated Digital Photography with a Colour Chart

⚬ Repeatability / Reproducibility:
  ⚬ Macbeth ColorChecker Mini (automatic colorimetric calibration across varied lighting and camera settings on wound images and chart patches): Van Poucke et al. (2010) reported both reproducibility (\Delta E^*_{ab} between repeated measurements) and accuracy against a spectrophotometer:
    "The reproducibility, visualized by the probability distribution of the dE_ab errors between 2 measurements of the patches of the images has a median of 3.43 dE* for all calibrated images, 23.26 dE_ab for all uncalibrated images. If we restrict ourselves to the proper patches of normal calibrated images the median is only 2.58 dE_ab!" (DOI: 10.1186/1471-2342-10-7)
    "Colour differences between the measurements and real spectrophotometric measurements reveal median dE_ab values respectively 6.40 for the proper patches of calibrated normal images and 17.75 for uncalibrated images demonstrating an important improvement in accuracy after calibration." (DOI: 10.1186/1471-2342-10-7)
  ⚬ Pictocolor inCamera calibration + Adobe Photoshop L^*a^*b^* skin extraction (210 randomly ordered images, expert vs. novice rater): Sommers et al. (2013):
    "Results of ICCs for intra-rater agreement showed high levels of internal consistency reliability within each rater for the lasso technique (ICC ≥ 0.99) and somewhat lower, yet acceptable, level of agreement for the color sampler technique (ICC = 0.91 for expert, ICC = 0.81 for novice). Skin L*, skin b*, and labia L* values reached the highest level of agreement (ICC ≥ 0.92) and skin a*, labia b*, and vaginal wall b* were the lowest (ICC ≥ 0.64)." (DOI: 10.1111/srt.12072)
⚬ Smallest Lesion Size Tested: not found in retrieved excerpts (Van Poucke et al., 2010 evaluated ROIs on 40 wound photographs; Sommers et al., 2013 evaluated normal skin and genital tissue regions without reporting a minimum lesion diameter).
⚬ White / Hypopigmented Spots: not found as primary validation data in retrieved excerpts (Van Poucke et al., 2010 cited a 2004 European Journal of Dermatology vitiligo transplantation imaging paper, but that study's primary text and figures were not retrieved).
⚬ Manufacturer-Funded Flag: Funding disclosures were not found in retrieved excerpts for Van Poucke et al. (2010) or Sommers et al. (2013).

References

Arbache, S., Roth, D., Arbache, S. T., & Hirata, S. H. (2019). Original method to repigment achromic laser tattoo removal scars. Case Reports in Dermatology, 11, 140–144. https://doi.org/10.1159/000500709
Cited by: 13

Clarys, P., Alewaeters, K., Lambrecht, R., & Barel, A. O. (2000). Skin color measurements: Comparison between three instruments: The Chromameter®, the DermaSpectrometer® and the Mexameter®. Skin Research and Technology, 6, 230–238. https://doi.org/10.1034/j.1600-0846.2000.006004230.x
Cited by: 553

Deda, A., Lipka-Trawińska, A., Błońska-Fajfrowska, B., et al. (2024). Methods of quantitative assessment of the response of dilated skin blood vessels to high-energy light treatments. Journal of Clinical Medicine, 13, 7547. https://doi.org/10.3390/jcm13247547
Cited by: 2

Hayashi, M., Okamura, K., Araki, Y., et al. (2017). Spectrophotometer is useful for assessing vitiligo and chemical leukoderma severity by quantifying color difference with surrounding normally pigmented skin. Skin Research and Technology, 24, 175–179. https://doi.org/10.1111/srt.12410
Cited by: 15

Hwang, S.-W., Kang, J.-H., Jung, S.-Y., et al. (2010). Vitiligo coexistent with nevus depigmentosus: This was treated with narrow-band UVB and these lesions were followed using the Mexameter®, a pigment-measuring device. Annals of Dermatology, 22, 482. https://doi.org/10.5021/ad.2010.22.4.482
Cited by: 13

Kanellis, V. G. (2019). A review of melanin sensor devices. Biophysical Reviews, 11, 843–849. https://doi.org/10.1007/s12551-019-00581-8
Cited by: 42

Kerckhove, E., Staes, F., Flour, M., Stappaerts, K., & Boeckx, W. (2001). Reproducibility of repeated measurements on healthy skin with Minolta Chromameter CR‐300. Skin Research and Technology, 7, 56–59. https://doi.org/10.1034/j.1600-0846.2001.007001056.x
Cited by: 69

Langeveld, M., van de Lande, L. S., O' Sullivan, E., van der Lei, B., & van Dongen, J. A. (2021). Skin measurement devices to assess skin quality: A systematic review on reliability and validity. Skin Research and Technology, 28, 212–224. https://doi.org/10.1111/srt.13113
Cited by: 79

Lee, K. C., Bamford, A., Gardiner, F., et al. (2019). Investigating the intra- and inter-rater reliability of a panel of subjective and objective burn scar measurement tools. Burns, 45, 1311–1324. https://doi.org/10.1016/j.burns.2019.02.002
Cited by: 88

Lipnick, M. S., Chen, D., Law, T., et al. (2025). Comparison of methods for characterizing skin pigment diversity in research cohorts. Cold Spring Harbor Laboratory. https://doi.org/10.1101/2025.02.21.25322707
Cited by: 19

Meng, X., & Xu, C.-C. (2020). Progress and prospect of non-invasive detection techniques in the therapeutic evaluation of melasma. Chinese Medical Journal, 133, 2104–2106. https://doi.org/10.1097/cm9.0000000000000984
Cited by: 6

Nedelec, B., Correa, J. A., Rachelska, G., Armour, A., & LaSalle, L. (2008). Quantitative measurement of hypertrophic scar: Intrarater reliability, sensitivity, and specificity. Journal of Burn Care & Research, 29, 489–500. https://doi.org/10.1097/bcr.0b013e3181710869
Cited by: 160

Park, E. S., Na, J. I., Kim, S. O., et al. (2006). Application of a pigment measuring device – Mexameter®– for the differential diagnosis of vitiligo and nevus depigmentosus. Skin Research and Technology, 12, 298–302. https://doi.org/10.1111/j.0909-752x.2006.00187.x
Cited by: 73

Sommers, M., Beacham, B., Baker, R., & Fargo, J. (2013). Intra‐ and inter‐rater reliability of digital image analysis for skin color measurement. Skin Research and Technology, 19, 484–491. https://doi.org/10.1111/srt.12072
Cited by: 38

van der Wal, M., Bloemen, M., Verhaegen, P., et al. (2013). Objective color measurements. Journal of Burn Care & Research, 34, e187–e194. https://doi.org/10.1097/bcr.0b013e318264bf7d
Cited by: 124

Van Poucke, S., Haeghen, Y. V., Vissers, K., Meert, T., & Jorens, P. (2010). Automatic colorimetric calibration of human wounds. BMC Medical Imaging, 10. https://doi.org/10.1186/1471-2342-10-7
Cited by: 49

Vasudevan, S., Vogt, W. C., Weininger, S., & Pfefer, T. J. (2024). Melanometry for objective evaluation of skin pigmentation in pulse oximetry studies. Communications Medicine, 4. https://doi.org/10.1038/s43856-024-00550-7
Cited by: 68

Weir, V. R., Dempsey, K., Gichoya, J. W., Rotemberg, V., & Wong, A.-K. I. (2024). A survey of skin tone assessment in prospective research. npj Digital Medicine, 7. https://doi.org/10.1038/s41746-024-01176-8
Cited by: 53

---

## Appendix 1. Quote check (checking thread, 2026-11-28)

Sources were fetched on 2026-11-28 through NCBI E-utilities (PubMed abstracts, PMC full text) and the Europe PMC API, and saved in the project files folder `papers/excerpts/` as `pmid_<PMID>.txt` and `pmc_<PMCID>.txt`. They are not committed. `tools/instrument_report_check.py` re-runs this check against those files.

Result: **25 quoted passages; 24 found verbatim, 0 altered, 1 not checkable.** "Verbatim" allows only these formatting differences, each noted in the table: a label's capital letters ("RESULTS:" in PubMed against "Results:" in the report), and a leading "- " or trailing full stop the report added to a table cell.

| # | Source (access) | Quote begins | Result |
|---|---|---|---|
| 1 | Meng 2020, PMID 32810046, PMC7478811 (FULL_TEXT) | "Moreover, good correlations..." | VERBATIM. But Meng is summarising "Ana et al[16]", which is Matias 2015 (doi:10.1111/srt.12199), the same closed paper PR 19 could not check. See Appendix 2, A1. |
| 2 | Weir 2024, PMID 39014060, PMC11252344 (FULL_TEXT) | "- Measurement area: 56 mm × 56 mm." | VERBATIM (Table 1 cell, Antera 3D row; the report added "- " and the full stop) |
| 3 | Arbache 2019, PMID 31182948, PMC6547281 (FULL_TEXT) | "Achromic laser tattoo scars. a, b Images..." | VERBATIM (figure legend) |
| 4 | Nedelec 2008, PMID 18388577 (ABSTRACT_ONLY) | "The ICC for the Mexameter erythema (>0.75)..." | VERBATIM |
| 5 | Langeveld 2021, PMID 34751474, PMC9299221 (FULL_TEXT) | "The Mexameter MX 18 and DSM II ColorMeter achieved..." | VERBATIM |
| 6 | Langeveld 2021 (FULL_TEXT) | "Intraobserver reliability was not tested..." | VERBATIM |
| 7 | Weir 2024 (FULL_TEXT) | "Measurement surface: 5 mm ≈ 19.6 mm²" | VERBATIM (Mexameter MX 18 row) |
| 8 | Deda 2024, PMID 39768469, PMC11727858 (FULL_TEXT) | "In this study, the analyzed skin area was approximately 19.6 mm2..." | VERBATIM (Mexameter section) |
| 9 | Park 2006, PMID 17026663 (ABSTRACT_ONLY) | "A selection of 202 hypopigmented skin lesions..." | VERBATIM |
| 10 | Park 2006 (ABSTRACT_ONLY) | "The mean RMI of ND lesions was 74+/-13..." | VERBATIM |
| 11 | Hwang 2010, PMID 21165227, PMC2991734 (ABSTRACT_ONLY; PMC holds the abstract only) | "Improvements in the two lesions were assessed..." | VERBATIM |
| 12 | Hayashi 2017, PMID 29057565 (ABSTRACT_ONLY) | "Results: MX18 and CM-700d can quantitatively distinguish..." | VERBATIM (PubMed prints "RESULTS:") |
| 13 | Hayashi 2017 (ABSTRACT_ONLY) | affiliation "Japan Tissue Engineering Co., Ltd., Gamagori, Aichi, Japan" | VERBATIM (affiliation 2, held by 3 of the 11 listed authors: Suzuki M, Tanaka T, Inoie M) |
| 14 | Van den Kerckhove 2001, PMID 11301642 (ABSTRACT_ONLY) | "Results: Results showed excellent values for ICC..." | VERBATIM (PubMed prints "RESULTS:") |
| 15 | Langeveld 2021 (FULL_TEXT) | "Interobserver reliability was highest for the Minolta Chromameter CR‐300..." | VERBATIM. But "60 patients" conflicts with the primary abstract. See Appendix 2, A3. |
| 16 | Langeveld 2021 (FULL_TEXT) | "Both Van den Kerckhove et al. and Uter et al. reported..." | VERBATIM (the report cuts the sentence at "0.954,"; it continues "respectively)") |
| 17 | Weir 2024 (FULL_TEXT) | "- Measurement surface: 8 mm." | VERBATIM (CR-400 row; the report added "- " and the full stop) |
| 18 | Lee 2019, PMID 31327551, PMC6731390 (FULL_TEXT) | "In terms of pigmentation measurement, the DSM II L*..." | VERBATIM, but cut mid-sentence and the meaning changes. See Appendix 2, A5. |
| 19 | Lipnick 2025 preprint, PMID 40061342, PMC11888493 (FULL_TEXT) | "Among subjects with repeat skin measurements over time..." | VERBATIM (Results; not in the abstract) |
| 20 | Weir 2024 (FULL_TEXT) | "- Measurement surface: 8 mm and 3 mm." | VERBATIM (CM-700d row; the report added "- " and the full stop) |
| 21 | Kanellis 2019, PMID 31396804, PMC6874939 | "CM-2600d (Konica Minolta, Japan) Remittance spectroscopy at 390 nm..." | **NOT CHECKABLE.** Not in the abstract. PMC holds the abstract only (efetch db=pmc); Europe PMC fullTextXML HTTP 500 and its PDF render HTTP 403 (2026-11-28). Added to the paywall list. |
| 22 | Hayashi 2017 (ABSTRACT_ONLY) | "ΔE*ab seems to be a useful parameter..." | VERBATIM |
| 23 | Van Poucke 2010, PMID 20298541, PMC2850874 (FULL_TEXT) | "The reproducibility, visualized by the probability distribution..." | VERBATIM (abstract and full text). Context changes what it means. See Appendix 2, A8. |
| 24 | Van Poucke 2010 (FULL_TEXT) | "Colour differences between the measurements and real spectrophotometric measurements..." | VERBATIM |
| 25 | Sommers 2013, PMID 23551208, PMC3778111 (FULL_TEXT) | "Results of ICCs for intra-rater agreement..." | VERBATIM |

Bibliographic details: all 18 DOIs resolve to the paper named, and volume and pages match PubMed. One name is wrong in the reference list. The first author of the CR-300 paper is "Van den Kerckhove E", not "Kerckhove, E.". The "Cited by" counts are not checkable and are not used.

## Appendix 2. Numbers and labels outside the quotes, including the summary table

| # | Report says | Source says | Verdict |
|---|---|---|---|
| A1 | Antera 3D: "review notes higher repeatability than Mexameter/CL-400"; manufacturer funding "not found" | Meng 2020 attributes the finding to "Ana et al[16]" (reference 16 is Matias 2015, "comparison study between antera 3D, mexameter and colorimeter"). Langeveld 2021 says of the studies that gave no funding statement: "However, one of these studies was performed by a contract research organization, which developed the investigated device. 15". Its reference 15 is Matias AR et al. 2015, the same Antera comparison. | **Do not rely on.** The only support is second-hand from a closed primary paper. The one review that looked at funding says the study came from the developer of the device. The report's "not found" funding flag for Antera is wrong. |
| A2 | Mexameter MX 18 interobserver ICC 0.92–0.94, "ordinary skin" | Langeveld text and Table 5 give 0.92–0.94 for van der Wal 2013. The van der Wal abstract (PMID 23237819, ABSTRACT_ONLY) gives only "All three instruments provided reliable readings (intraclass correlation coefficient ≥ 0.83; confidence interval: 0.71-0.90) on normal skin and scar tissue", in "Fifty scars". | The figure is in the review; it is **not checkable at the primary** (full text needed). The label "ordinary skin" is not supported: the study measured normal skin and scar tissue. The same applies to DSM II 0.89–0.96, which the report's table labels "(normal skin)". |
| A3 | CR-300 interobserver 0.92–0.99 and intraobserver 0.98–0.99, from "60 patients" | Langeveld says "60 patients". The primary abstract says "healthy skin of 30 volunteers" and gives no ICC values. Langeveld Table 5 also lists an interinstrument ICC range of 0.99–0.999. The primary abstract says it also tested "repeated measurements with a 1 week time lapse" and reported "standard error of measurements (SEM)". | ICC ranges are as the review gives them. **Participant count contradicts the primary.** No SEM value is in the abstract (full text needed). |
| A4 | Uter et al. intraobserver 0.926–0.954 | In Langeveld text and Table 5 (CR-300, 2287 subjects, inner upper arm). Primary not fetched. | Review figure only. |
| A5 | DSM II "inter- and intra-rater ICC > 0.90 for L^* and Melanin (scars/normal skin)" | The sentence continues "...above 0.90 for both single and average measures". The Results say this of scar tissue, and that for normal skin the values were "although lower, ... above the set threshold of 0.70 (ICC Single or Average = 0.806–0.960)". Table 5, normal skin: L* inter-rater single ICC 0.806, Melanin 0.836. Intra-rater single L* is 0.90, not above it. | **Wrong for normal skin.** It holds for scar tissue only. All repeats were within one day: "3 different assessors 3 times over a period of one day". |
| A6 | DSM II smallest size "not found" | Lee 2019: the probe "has a skin measuring area of 4 mm in diameter". | The report missed this. 4 mm is the DSM II sampling area. |
| A7 | Spectrophotometers: Vasudevan "summarized literature repeatability at the aggregate level as ICC greater than 0.90 and/or absolute CV less than 10%" | "ICCs > 0.90 were considered to indicate excellent reliability ... whereas CVs <10% were considered excellent". Also: "excellent results (ICC > 0.90 and/or \|CV \| < 10%) were obtained in approximately 85%, 75%, and 67% of intra-observer, inter-observer, and inter-instrument studies, respectively." | **Meaning changed.** These are the review's grading thresholds, not a summary result. About a third of inter-instrument studies fell short of them. The device list (CM600d, CM700d, CM-2002, DSM III, DSM IV) is verified. |
| A8 | Calibrated photography: 3.43 / 2.58 / 23.26 ΔE*ab "on wound images and chart patches" | These figures come from experiment 1, on the "MacBeth Colour Checker Chart Mini" patches, "Based on 39 images taken with a Nikon D200 and 15 images with a Canon 10D under different illuminants and settings", saved "in high-quality jpeg mode". The 40 wound images belong to experiment 2, whose result appears only as a figure. | Numbers verbatim, but **they measure chart patches, not skin or wounds**, and they come from JPEG files, not RAW. |
| A9 | Lipnick: "CM-700d/objective", "ICU", "hospitalized subjects" | The 11.9° sentence is about "objective assessment", with no device named. The study used the CM-700d and the Delfin SkinColorCatch, and "The DSCC and VL were only used in the ICU cohort". The same paper gives within-session repeats: "Assessment of triplicate measurements at the forehead for the same participant showed a mean ΔITA of 0.8 ± 1.6 and ΔE 0.6 ± 0.6 for the KM-700d, and ΔITA 1.0 ± 1.8 and ΔE 1.4 ± 1.0 for the DSCC." | The figure is verbatim. Its device attribution and cohort are not stated in that sentence. Within-session figures that the report missed are quoted here. |
| A10 | Clarys 2000 "evaluated MX 16" and "CR-200" | The abstract names "Chromameter from Minolta", "DermaSpectrometer from Cortex" and "Mexameter from Courage-Khazaka", with no model numbers. It says repeatability is "rather good". | The model numbers are not in the abstract (full text needed). The report is right that no figures are available. |
| A11 | Funding "not found" for most papers | Disclosures are printed in the full texts. Meng: "supported by a grant from the National Natural Science Foundation of China". Weir: competing interests listed, none naming a colour-device maker. Langeveld: "The authors received no specific funding for this work." Deda: "The authors declare no conflicts of interest." Lee: "The Scar Free Foundation ... and the Wellcome Trust". Lipnick: FDA and foundations, and "No company provided any direct funding for this study". Van Poucke and Vasudevan: no competing interests. Sommers: US NIH grants. **Arbache 2019: "The first author is the owner of Traderm" and "The tattooing machine, cartridges, and drug used in this study were supplied by Traderm".** | **The report's flags are incomplete.** Of the readable papers, none is funded by a colour-instrument maker. Arbache 2019 has a commercial interest in the treatment device (not the Antera) that the report did not flag. Matias 2015 is flagged in A1. |
| A12 | Hayashi: CM-700d "evaluated on vitiligo and chemical leukoderma"; the leukoderma was "chemical" | Abstract: "rhododendrol ... -induced leukoderma". | Verified from the abstract. The aperture used and any repeatability figures are not in the abstract (full text needed). |

## Appendix 3. How the checked figures bear on the measurement plan (checking thread's judgment, not the report's)

The plan measures delta L* between a fixed disc inside the spot and a ring of surrounding skin, corrected with a colour card. Its target of 1.0 L* on a 2 mm spot is the project's own goal. The plan is not edited here.

1. **Every contact instrument in the report samples an area wider than a 2 mm spot.** The checked apertures are: CM-700d "8 mm and 3 mm" (Weir), DSM II "4 mm in diameter" (Lee), Mexameter "5 mm ≈ 19.6 mm²" (Weir, Deda) and CR-400 "8 mm" (Weir). None of these can read the inside of a 2 mm spot without picking up surrounding skin. This supports PR 19's advice not to buy a CM-700d, and adds that a DSM II or Mexameter would not help either.
2. **Only one checked figure is in L* units, and it is not clean.** Lee 2019 Table 5 gives DSM II L* on normal skin, same-day repeats, 4 mm probe: "%CV (SEM)" of "8.10 (1.63)" inter-rater and "5.20 (1.03)" intra-rater. The paper defines SEM as "Standard Error of Mean". The figures do not reconcile with the table's own mean of 37.67 [1.63 / 37.67 is 4.3%, not 8.10%], and that mean lies outside its own stated IQR of "37.75–43.34". [If 1.03 and 1.63 are L* units, a contact device's same-day error on normal skin is already at or above the plan's 1.0 L* target, on an area four times the spot's diameter.] This is a lead only. It needs the authors or the supplementary data to settle the unit.
3. **ICC values cannot be put in L* units.** An ICC depends on how much people differ from each other, as well as on measurement error. A high ICC across people with different skin tones does not show a small error in L*. None of the ICCs in this report (Mexameter, CR-300, DSM II, Sommers' photo method) tells us whether a change of 1.0 L* inside one spot is detectable. Van den Kerckhove 2001 did report an SEM for CR-300 with a one-week repeat, which would be in instrument units, but the value is not in the abstract (full text needed, paywalled).
4. **Calibrated photography figures are about the card, and they are larger than the target.** Van Poucke's median 2.58 ΔE*ab between two measurements of the same chart patches (proper patches, normal images) came from JPEG files under deliberately varied light. [Because ΔE*ab includes ΔL*, the L* part of that error is at most the full ΔE*ab, but the paper does not report it separately.] The plan's controlled RAW capture with one light source is a different and tighter setup. PR 45 already records a closer figure: card-only ΔE drift under 1 over four weeks with the same ColorChecker Nano.
5. **Use on white spots: three device families have been used, but none has repeatability data on them.** The Mexameter was used on vitiligo and nevus depigmentosus (Park 2006, 202 lesions; lesion-to-control melanin ratios of "50+/-24" for vitiligo). The CM-700d and Mexameter were used on vitiligo and rhododendrol leukoderma (Hayashi 2017, abstract only). The Antera 3D was used on achromic tattoo-removal scars (Arbache 2019, one case figure). None of them is IGH, and none reports a test-retest figure measured on a white spot.
6. **A day-to-day ITA figure is not a measurement error.** Lipnick's "mean range of ITA across study days of 11.9°" combines biology and instrument across days in an oximetry cohort. ITA combines L* and b*, so it cannot be converted to L* without b*. The within-session CM-700d figure from the same paper, "ΔE 0.6 ± 0.6" at the forehead, is close to what PR 19 found for the CM-700d (0.37 to 0.63 ΔE*ab), with an 8 or 3 mm aperture not stated in that sentence.

**Net effect on the plan:** nothing checked here gives a between-visit L* error on a spot of 2 mm or smaller. Plan section 2.3 stands: the 1.0 L* target remains the project's own design goal. Nothing in the report argues for buying a contact instrument.

**Do not rely on:** the Antera "higher repeatability" claim (A1); "ordinary skin" or "normal skin" labels on the van der Wal and Lee ICCs (A2, A5); Vasudevan's thresholds read as results (A7); Van Poucke's figures read as skin or wound reproducibility (A8); the CM-2600d 8 mm aperture (not checkable); Langeveld's "60 patients" for Van den Kerckhove (A3).
