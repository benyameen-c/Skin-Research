# External report: objective colour measurement of small skin lesions (ChatGPT deep research)

**Origin.** Written by ChatGPT deep research from a copy-paste prompt the project gave Ben (prompt 2, skin colour measurement tools). Ben pasted it into the project thread on 2026-11-28 at 00:50 UTC; the file name carries the date the prompt was given (2026-11-27).

**Status: UNVERIFIED LEADS.** Nothing below has entered `data/evidence.csv`. Under CLAUDE.md rule 9, every claim here is a lead until a primary source is quoted. The quote check of the priority numbers is in the appendix at the end of this file, and a comparison with `content/measurement-tool-plan.md` follows it. The comparison is the checking thread's judgment, not part of the report.

**Fidelity.** The report text between the two horizontal rules is as Ben pasted it, except that HTML entities introduced in transit (`&amp;`, `&lt;`, `&gt;`) are written as the characters they stand for. Typographic quotes, asterisks and links are unchanged.

---

# Objective colour measurement of small skin lesions

## Executive conclusion

For lesions at the smaller end of the requested range, the strongest direct instrument evidence is for the Konica Minolta CM‑700d using its “3 mm” aperture. Human-skin repeatability was a mean “0.39” ΔE\*ab without repositioning and “0.63” ΔE\*ab when measurements were repeated consecutively; these are repeatability estimates, not formal longitudinal smallest-detectable-change values. The study also found that changing aperture or contact pressure could move the result by “2.48”–“3.04” ΔE\*ab, which is larger than many plausible biological changes ([Wang et al., DOI 10.1002/col.22230](https://doi.org/10.1002/col.22230)).

For measurements derived from photographs, Antera 3D has the best combination of published skin-colour repeatability and built-in follow-up registration that I found: reported median coefficients of variation were “0.36%” for L\*, “1.56%” for a\*, and “0.58%” for b\*. However, neither a minimum valid ROI diameter nor a formal L\*/ΔE smallest detectable change was reported ([Matias et al., DOI 10.1111/srt.12199](https://doi.org/10.1111/srt.12199); [Antera product datasheet](https://miravex.com/wp-content/uploads/2018/04/Antera-3D-CS.pdf)).

For an open workflow, the best-supported design is controlled RAW photography with a colour card in every session, followed by card detection, colour correction, local registration, and calculation of lesion-versus-surrounding-skin ΔE. The strongest clinical calibration study reported whole-process reproducibility averaging “3.7” ΔE\*ab with a “10.4” 99th percentile; it cautioned that an absolute image colour change needed to exceed “10” ΔE\*ab to be considered significant under that particular workflow. Within-image lesion/background comparisons were more stable, supporting the use of a differential endpoint rather than absolute lesion L\* alone ([Vander Haeghen & Naeyaert, DOI 10.1001/archderm.142.1.42](https://doi.org/10.1001/archderm.142.1.42)).

Across the reviewed methods, a formal longitudinal smallest detectable change in L\* or ΔE was usually **not found**. Manufacturer white-tile repeatability, same-session MCDM, coefficients of variation, ICCs, and area-score SDCs should not be presented as equivalent to longitudinal colour SDC.

## 1. Clinical colorimeters and spectrophotometers

These devices are useful reference methods, but they measure skin directly rather than deriving colour from photographs.

### Konica Minolta CM‑700d and CM‑700d‑U

**Manufacturer claims**

The CM‑700d specification gives measurement/illumination diameters of “8/11 mm” for MAV and “3/6 mm” for SAV. White-tile repeatability is specified as chromaticity standard deviation “ΔE\*ab 0.04,” while inter-instrument agreement is “ΔE\*ab 0.2” under the stated calibration conditions ([CM‑700d product datasheet](https://sensing.konicaminolta.us/us/products/cm-700d-spectrophotometer/)).

The CM‑700d‑U software manual lists a fixed “USAV (2.4mm),” but I found no independent human-skin validation for that aperture ([SpectraMagic NX2 manual](https://sensing.konicaminolta.us/wp-content/uploads/SMNX2-Manual-version-1.2-min.pdf)).

**Independent validation**

In human skin, the CM‑700d’s mean color difference from the mean was “0.39” ΔE\*ab with the “3 mm” aperture and “0.35” with the larger aperture. Continuous measurements averaged “0.37,” whereas measurements involving consecutive replacement averaged “0.63.” The best tested configuration reached “0.34.” These values quantify same-session repeatability, not a months-apart detection threshold ([Wang et al., DOI 10.1002/col.22230](https://doi.org/10.1002/col.22230)).

Changing aperture produced mean differences of “2.48” or “3.04” ΔE\*ab depending on pressure; changing pressure with the small aperture produced “1.82.” Longitudinal studies therefore need the same mask, contact pressure, anatomical orientation, calibration procedure, and operator technique at every visit ([Wang et al., DOI 10.1002/col.22230](https://doi.org/10.1002/col.22230)).

**Smallest detectable change:** not found. The closest published values are the MCDM repeatability figures above.

### Konica Minolta CR‑400

**Manufacturer claims**

The CR‑400 datasheet specifies an “8 mm” measurement area, “11 mm” illumination area, white-plate repeatability of “ΔE\*ab 0.07,” and inter-instrument agreement of “ΔE\*ab 0.6” ([CR‑400 datasheet](https://sensing.konicaminolta.us/wp-content/uploads/cr400_catalog_eng-4i80526wf5.pdf)).

**Independent validation**

A systematic review stated that the CR‑400 “has not yet been evaluated in clinical research”; older CR‑300 studies cannot automatically validate the newer model. The review reported legacy CR‑300 intraobserver ICCs of “0.926–0.954” and other studies’ interobserver values of “0.92–0.99,” but these are reliability coefficients rather than error in L\* units ([Ly et al., DOI 10.1111/srt.13113](https://doi.org/10.1111/srt.13113)).

**Smallest detectable change:** not found.

### Courage + Khazaka Skin-Colorimeter CL 400

**Manufacturer claims**

The brochure specifies a “5 mm” measuring area inside an illuminated area of approximately “17 mm” and states measurement inaccuracy of “±5%.” It reports CIE XYZ and L\*a\*b\*-related outputs, while noting that some displayed values are instrument indices ([CL 400 brochure](https://www.courage-khazaka.com/images/Downloads/Brochures/Wissenschaftlich/Prospekt_ColorimeterCL400.pdf)).

**Independent validation**

Against Antera 3D after controlled UV exposure, median CL 400 coefficients of variation were “0.66%” for L\*, “3.06%” for a\*, and “2.01%” for b\*. Antera was more repeatable in the same experiment ([Matias et al., DOI 10.1111/srt.12199](https://doi.org/10.1111/srt.12199)).

**Smallest detectable change:** not found. A coefficient of variation cannot be converted into a universal L\* threshold without the underlying mean, variance structure, and longitudinal protocol.

### Cortex DSM‑4 and earlier DSM II

**Manufacturer claims**

The current DSM‑4 specifies an aperture of “50 mm² (8 mm dia.)” but a smaller actual measurement area of “14 mm² (4.2 mm dia.).” The manufacturer lists “ΔEab <2” and “ΔE00 <1”; the page does not identify these values as a formal human longitudinal SDC ([Cortex DSM‑4 product specification](https://www.cortex.dk/skin-analysis/colorimeter-dsm-4/)).

**Independent validation**

For the earlier DSM II, normal-skin and scar measurements had single-measure interobserver ICCs of at least “0.83”; DSM II L\* ICCs were “0.95” on normal skin and “0.94” on scars. The corresponding L\* coefficients of variation were “4.0%” and “5.9%” ([van der Wal et al., DOI 10.1097/BCR.0b013e318264bf7d](https://doi.org/10.1097/BCR.0b013e318264bf7d)). Independent validation specifically transferring those results to the DSM‑4 was **not found**.

**Smallest detectable change:** not found.

## 2. Dermoscopy and total-body photography software

### Antera 3D

Antera acquires a “56 × 56 mm” field using multispectral illumination, outputs L\*a\*b\* and colour-difference measurements, and includes proprietary Spot‑On registration for matching follow-up images ([Antera datasheet](https://miravex.com/wp-content/uploads/2018/04/Antera-3D-CS.pdf); [system review, PMCID PMC11252344](https://pmc.ncbi.nlm.nih.gov/articles/PMC11252344/)). Its validated repeatability is given above, but minimum reliable lesion/ROI size, registration error in millimetres, and L\*/ΔE SDC were **not found**.

### FotoFinder Moleanalyzer pro

Moleanalyzer pro reports lesion colours, borders, symmetry, structures, size and diameter, but the product literature does not document calibrated CIELAB lesion-versus-background output ([FotoFinder product page](https://www.fotofinder-systems.com/products/fotofinder-ai/moleanalyzer-pro)). The safety documentation says AI assessment should not be used below “2 mm” or above “20 mm,” while the user manual states that segmentation and parameter accuracy cannot be claimed ([FotoFinder safety information](https://www.fotofinder.de/fileadmin/user_upload/11_Footer/FotoFinder_Systems_Information_Brochure_of_performance_and_safety_EN_Apr_2024.pdf); [Moleanalyzer manual](https://www.fotofinder-systems.com/fileadmin/Documentation/IFU_Moleanalyzer_pro_6.1_20240610_EN.pdf)).

Its “colour” feature is therefore primarily a diagnostic-image descriptor, not validated longitudinal colorimetry. L\*/ΔE repeatability and SDC were **not found**.

### MoleMax HD

MoleMax provides serial dermoscopy, lesion segmentation and diagnostic scoring, including ABCD-type colour features, but the manual does not specify calibrated CIELAB output or ΔE repeatability ([MoleMax HD manual](https://www.molemaxsystems.com/wp-content/uploads/2020/10/MoleMax-HD-1.6-English.pdf)). Minimum colour-analysis ROI, L\*/ΔE repeatability and SDC were **not found**.

### VECTRA WB360 and DermaGraphix

VECTRA WB360 uses “46” stereo pods and supports markerless lesion tracking, guided follow-up and attachment of close-up dermoscopy images to a whole-body model ([Canfield product page](https://iveos.canfieldsci.com/imaging-systems/vectra-wb360-imaging-system/)). I found no product claim or validation study establishing CIELAB accuracy or ΔE repeatability.

A research algorithm using longitudinal total-body models reported “90.1%” localization success under a “10 mm” criterion and “98.1%” matching accuracy for subjects with more than “200” lesions. That criterion is too coarse to prove re-localization of a particular very small lesion without a second-stage close-up match ([Huang et al., DOI 10.1016/j.media.2026.103963](https://doi.org/10.1016/j.media.2026.103963)).

## 3. Validated pigmentation and vitiligo image scores

These methods are useful clinical outcomes, but none supplies a validated L\*/ΔE detection threshold for a tiny lesion.

- **Skin Hyperpigmentation Index:** SHI derives a lesion-to-reference pigmentation ratio from dermoscopic images and was initially validated for hyperpigmented lesions ([PMID 32103550; DOI 10.1111/jdv.16312](https://pubmed.ncbi.nlm.nih.gov/32103550/)). A subsequent pigmented-lesion study reported excellent intra- and inter-rater reliability, though the abstract gives no numerical L\*/ΔE error ([PMID 34969031; DOI 10.1159/000520753](https://pubmed.ncbi.nlm.nih.gov/34969031/)). In melasma, mapped SHI had an ICC of “0.87,” with concordance of “0.48,” “0.45,” and “0.60” against three clinical pigmentation scales ([DOI 10.1111/jocd.15866](https://doi.org/10.1111/jocd.15866)). SHI is an ordinal pigmentation index, not CIELAB; colour SDC is **not found**.

- **Digital Image Analysis System for vitiligo:** comparison of digital analysis with clinician estimation across “21” patches produced an ICC of “0.83” for percentage repigmentation ([PMID 22621363; DOI 10.1111/j.1468-3083.2012.04568.x](https://pubmed.ncbi.nlm.nih.gov/22621363/)). This measures repigmented area, not lesion-versus-skin ΔE.

- **Computerized DIAS:** lesions were photographed every “6 weeks” for “24 weeks,” but agreement with physician global assessment was only κ “0.17” ([PMID 25367709; DOI 10.1111/ajd.12247](https://pubmed.ncbi.nlm.nih.gov/25367709/)). No colour SDC was reported.

- **Vitiligo Extent Score:** test–retest ICC was “0.943,” compared with “0.904” for VASI. For limited disease, the reported SDC95 was “1.31%” body-surface area for VES and “1.85%” for VASI ([PMID 26827762; DOI 10.1016/j.jid.2015.12.040](https://pubmed.ncbi.nlm.nih.gov/26827762/)). Those are extent changes, not L\* or ΔE thresholds.

- **Photography-based pigmentation-area measurement:** agreement with clinician consensus averaged “92.1%,” with standard deviation “4.6%,” in a study of facial pigmentation photographs ([PMID 26705766; DOI 10.1111/ics.12303](https://pubmed.ncbi.nlm.nih.gov/26705766/)). It measures affected area rather than colour magnitude.

## 4. Open-source colour calibration

A reproducible open pipeline can be assembled from:

1. RAW decoding with [rawpy/LibRaw](https://github.com/letmaik/rawpy).
2. Card localization with [colour-checker-detection](https://github.com/colour-science/colour-checker-detection).
3. Polynomial or matrix colour correction and CIELAB/ΔE calculation with [Colour](https://github.com/colour-science/colour).
4. Alternatively, chart correction through [OpenCV’s Color Correction Model](https://docs.opencv.org/4.x/d1/dc1/tutorial_ccm_color_correction_model.html).
5. Feature-based and deformable registration with [OpenCV](https://github.com/opencv/opencv) or [scikit-image](https://github.com/scikit-image/scikit-image).

The repositories provide the necessary algorithms, but I found no skin-specific validation of that exact combined stack. Its accuracy therefore depends on the camera, RAW pipeline, illumination, chart, calibration model, glare control and capture geometry.

The best clinical calibration benchmark I found reported:

- Repeated calibration of the same image: mean “0.4” and 99th percentile “1.2” ΔE\*ab.
- Complete calibrated-image reproducibility: mean “3.7” and 99th percentile “10.4” ΔE\*ab.
- Absolute agreement with a spectrophotometer: mean “5.1” and 99th percentile “15.4” ΔE\*ab.
- Same-skin repeat photographs under two conditions: “1.5” and “2.9” ΔE\*ab.
- A suggested absolute-image significance threshold greater than “10” ΔE\*ab.

All are from one controlled system and should not be transferred to a new camera without an internal repeatability study ([Vander Haeghen & Naeyaert, DOI 10.1001/archderm.142.1.42](https://doi.org/10.1001/archderm.142.1.42)).

A current ColorChecker Passport is listed at “$119.00” by its manufacturer ([Calibrite product page](https://calibrite.com/us/product/colorchecker-passport-photo-2/)). A full-size card may not fit beside a small lesion; using a separate card photograph under supposedly identical lighting is weaker than having an in-frame reference. Independent CIELAB accuracy for miniature or custom skin-tone cards was **not found**.

## 5. Smartphone-based approaches

### Generic colour-picker applications

In human forehead measurements against a MiniScan reference, Color Grab and Color Picker produced absolute errors of “7.59” and “7.65” ΔE00. Relative-colour trueness was “3.79” and “3.70,” while within-method MCDM precision was “1.34” and “0.96.” Thus, apparently good repeatability did not imply good absolute accuracy ([Niakan et al., PMID 39627966; DOI 10.1111/jopr.13970](https://pubmed.ncbi.nlm.nih.gov/39627966/)).

**Formal L\*/ΔE SDC:** not found.

### Smartphone photographs normalized against Antera

In smartphone selfies compared with Antera 3D, the best reported correlations after CLAHE processing were “0.628” for L\* and “0.860” for a\*, while b\* remained “−0.421.” The study concerned broad facial skin rather than very small lesions and did not establish a ΔE detection threshold ([Smeaton et al., PMID 32726869; DOI 10.1111/srt.12928](https://pubmed.ncbi.nlm.nih.gov/32726869/)).

### Smartphone plus dermoscope and colour chart

A calibrated smartphone-dermoscope study reported ColorChecker CIE76 errors of “3.19” for one phone and “1.76” for another, with within-phone variability as low as “0.12.” This was primarily a laboratory and canine-skin validation, not human longitudinal lesion validation ([DOI 10.3390/s20216234](https://doi.org/10.3390/s20216234)).

### Multispectral smartphone prototype

A research prototype found approximately “ΔL* ≈ 3” and “Δa* ≈ 3” between a nevus and its surrounding skin and projected a high-volume bill of materials below “$40” excluding the phone. The authors explicitly said longitudinal clinical validation was still required ([PMID 32578406; DOI 10.1117/1.JBO.25.6.066004](https://pubmed.ncbi.nlm.nih.gov/32578406/)).

### Capture sensitivity

A controlled smartphone study found that viewing angle altered L\*, a\* and b\*, while distance altered L\*, with standard errors exceeding “1 CIELAB unit”; RAW DNG files were less variable than processed JPEGs ([Cronin et al., DOI 10.1002/jbio.202200381](https://doi.org/10.1002/jbio.202200381)). A smartphone protocol should therefore lock exposure, focus, white balance, distance, angle, illumination and processing, and should preserve RAW data where available.

## 6. Re-locating and registering the same lesion

Three distinct registration problems must be handled:

1. **Body-site relocation:** find the same lesion again.
2. **Close-up registration:** align the follow-up photograph to baseline.
3. **ROI correspondence:** ensure that lesion and surrounding-skin masks sample the same tissue.

Serial dermoscopy standards recommend a persistent lesion identifier and links between close-up and regional images; this provides traceability but not automatic millimetre-level registration ([DICOM dermoscopy workflow](https://dicom.nema.org/medical/dicom/current/output/chtml/part17/sect_TTTT.3.2.html)). Vitiligo photography recommendations likewise emphasize standardized serial acquisition ([PMID 31678332; DOI 10.1016/j.jaad.2019.10.055](https://pubmed.ncbi.nlm.nih.gov/31678332/)).

For close-up dermoscopic pairs, a feature-registration method tested on “10” lesions reported mean error of “0.23 mm” in estimated diameter evolution; performance deteriorated as the interval between photographs increased ([Navarro et al., PMID 29993849; DOI 10.1109/JBHI.2018.2825251](https://pubmed.ncbi.nlm.nih.gov/29993849/)). This is the most directly relevant published spatial-error figure I found, but it presupposes that the correct lesion has already been photographed.

A practical, evidence-aligned protocol is therefore:

- Capture a regional anatomical image containing stable landmarks and a persistent lesion identifier.
- Capture a perpendicular macro/dermoscopic image at fixed distance with scale and colour reference.
- Register follow-up to baseline first with rigid or affine feature matching, then use a local deformable correction only if needed.
- Segment the lesion at baseline and follow-up, erode the lesion boundary to limit mixed pixels, and define a surrounding annulus that excludes hair, glare, vessels and other lesions.
- Use the within-image lesion-to-annulus difference at each visit as the primary endpoint; report both ΔL\* and ΔE00.
- Establish a study-specific SDC from repeated complete acquisitions—including repositioning—before interpreting biological change.

The last recommendation is an inference from the aperture/pressure sensitivity of contact instruments, the whole-process error of calibrated photography, and the published registration errors rather than a currently validated universal standard ([Wang et al.](https://doi.org/10.1002/col.22230); [Vander Haeghen & Naeyaert](https://doi.org/10.1001/archderm.142.1.42); [Navarro et al.](https://doi.org/10.1109/JBHI.2018.2825251)).

| Method | Indicative cost range | Smallest aperture or reported spot size | Repeatability or closest performance figure | Reported L\*/ΔE smallest detectable change | Validation study | Open or proprietary |
|---|---:|---:|---|---|---|---|
| Konica Minolta CM‑700d | Public listing “$6,749.93” ([product listing](https://spwindustrial.com/konica-minolta-cm-700d-portable-spectrophotometer-w-software-accessories/)) | SAV “3/6 mm”; CM‑700d‑U “2.4mm” manufacturer-only ([datasheet](https://sensing.konicaminolta.us/us/products/cm-700d-spectrophotometer/); [manual](https://sensing.konicaminolta.us/wp-content/uploads/SMNX2-Manual-version-1.2-min.pdf)) | Human skin MCDM “0.39” at the small aperture; “0.63” with consecutive replacement ([DOI](https://doi.org/10.1002/col.22230)) | **Not found**; MCDM is not SDC | Human skin, pressure and aperture study ([DOI 10.1002/col.22230](https://doi.org/10.1002/col.22230)) | Proprietary |
| Konica Minolta CR‑400 | Public listings “$9,972.00”–“$13,544.34” ([Genlab](https://www.genlabdirect.com/konica-minolta-sensing-americas-cr-400-colorimeter-package-with-dpu-7600-0000-1767); [Fisher](https://www.fishersci.com/shop/products/NC2905717/NC2905717)) | Measurement “8 mm”; illumination “11 mm” ([datasheet](https://sensing.konicaminolta.us/wp-content/uploads/cr400_catalog_eng-4i80526wf5.pdf)) | Manufacturer white-tile “ΔE*ab 0.07”; clinical CR‑400 validation not found | **Not found** | Review reports CR‑400 not clinically evaluated; legacy CR‑300 only ([DOI 10.1111/srt.13113](https://doi.org/10.1111/srt.13113)) | Proprietary |
| C+K CL 400 | **Not found** | Measuring area “5 mm” ([brochure](https://www.courage-khazaka.com/images/Downloads/Brochures/Wissenschaftlich/Prospekt_ColorimeterCL400.pdf)) | L\* CV “0.66%,” a\* “3.06%,” b\* “2.01%” ([DOI](https://doi.org/10.1111/srt.12199)) | **Not found** | UV-exposed human skin comparison with Antera ([PMID 25645051](https://pubmed.ncbi.nlm.nih.gov/25645051/)) | Proprietary |
| Cortex DSM‑4 | **Not found** | Aperture “8 mm”; actual measurement area “4.2 mm” ([product specification](https://www.cortex.dk/skin-analysis/colorimeter-dsm-4/)) | Manufacturer claims “ΔE00 <1”; independent DSM‑4 repeatability not found | **Not found** | Earlier DSM II had L\* ICC “0.95” on normal skin ([DOI 10.1097/BCR.0b013e318264bf7d](https://doi.org/10.1097/BCR.0b013e318264bf7d)) | Proprietary |
| Antera 3D | **Not found** | Field “56 × 56 mm”; minimum valid ROI **not found** ([review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11252344/)) | L\* CV “0.36%,” a\* “1.56%,” b\* “0.58%” ([DOI](https://doi.org/10.1111/srt.12199)) | **Not found** | Controlled human UV-exposure study ([PMID 25645051](https://pubmed.ncbi.nlm.nih.gov/25645051/)) | Proprietary |
| FotoFinder Moleanalyzer pro | **Not found** | AI range begins at “2 mm”; colour-calibration spot size **not found** ([safety information](https://www.fotofinder.de/fileadmin/user_upload/11_Footer/FotoFinder_Systems_Information_Brochure_of_performance_and_safety_EN_Apr_2024.pdf)) | CIELAB/ΔE repeatability **not found** | **Not found** | Diagnostic feature analysis, not validated colorimetry ([product page](https://www.fotofinder-systems.com/products/fotofinder-ai/moleanalyzer-pro)) | Proprietary |
| MoleMax HD | **Not found** | **Not found** | CIELAB/ΔE repeatability **not found** | **Not found** | Diagnostic dermoscopy scoring only in available manual ([manual](https://www.molemaxsystems.com/wp-content/uploads/2020/10/MoleMax-HD-1.6-English.pdf)) | Proprietary |
| VECTRA WB360 | Independent review: “upwards of €70,000” ([DOI 10.3389/fphot.2025.1535133](https://doi.org/10.3389/fphot.2025.1535133)) | Colour-analysis spot size **not found** | Research localization “90.1%” at a “10 mm” criterion ([DOI](https://doi.org/10.1016/j.media.2026.103963)) | **Not found** | Large longitudinal 3D lesion-matching study; no CIELAB validation ([DOI 10.1016/j.media.2026.103963](https://doi.org/10.1016/j.media.2026.103963)) | Proprietary |
| Open RAW + ColorChecker workflow | Card listed at “$119.00,” plus camera/lighting ([Calibrite](https://calibrite.com/us/product/colorchecker-passport-photo-2/)) | Pixel/ROI dependent; validated minimum lesion size **not found** | Whole-process mean “3.7” and 99th percentile “10.4” ΔE\*ab ([DOI](https://doi.org/10.1001/archderm.142.1.42)) | Study suggested absolute change “>10” ΔE\*ab; not a universal SDC | Controlled calibrated clinical photography ([DOI 10.1001/archderm.142.1.42](https://doi.org/10.1001/archderm.142.1.42)) | Open software; proprietary card/camera |
| Smartphone Color Grab/Color Picker | App/device cost **not found** | Spot size **not found** | MCDM “1.34” and “0.96” ΔE00; absolute errors “7.59” and “7.65” ([DOI](https://doi.org/10.1111/jopr.13970)) | **Not found** | Human forehead against MiniScan reference ([PMID 39627966](https://pubmed.ncbi.nlm.nih.gov/39627966/)) | Proprietary apps |
| Calibrated smartphone + dermoscope | Study system approximately “$300” ([DOI](https://doi.org/10.3390/s20216234)) | Optics dependent; minimum human lesion size **not found** | Laboratory CIE76 error “1.76”–“3.19”; within-phone variability as low as “0.12” | **Not found** | Colour-chart and canine-skin validation, not human longitudinal validation ([DOI 10.3390/s20216234](https://doi.org/10.3390/s20216234)) | Mixed proprietary hardware/software |
| Smartphone multispectral prototype | Projected BOM “<$40” excluding phone ([DOI](https://doi.org/10.1117/1.JBO.25.6.066004)) | **Not found** | Demonstrated lesion contrast “ΔL* ≈ 3” and “Δa* ≈ 3”; repeatability not reported | **Not found** | Prototype study explicitly requiring longitudinal validation ([PMID 32578406](https://pubmed.ncbi.nlm.nih.gov/32578406/)) | Research prototype |
| SHI dermoscopic pigmentation score | **Not found** | Supports small dermoscopic ROIs; numerical minimum **not found** | Mapped melasma ICC “0.87” ([DOI](https://doi.org/10.1111/jocd.15866)) | **Not applicable/not found**; output is an index, not L\*/ΔE | Pigmented-lesion and melasma validations ([DOI 10.1111/jdv.16312](https://doi.org/10.1111/jdv.16312); [DOI 10.1111/jocd.15866](https://doi.org/10.1111/jocd.15866)) | Public calculator; implementation proprietary/not fully open |
| Vitiligo DIAS/VES | **Not found** | Lesion-size floor **not found** | DIAS ICC “0.83”; VES test–retest ICC “0.943” ([DOI](https://doi.org/10.1111/j.1468-3083.2012.04568.x); [DOI](https://doi.org/10.1016/j.jid.2015.12.040)) | **Not applicable**; VES SDC “1.31%” is body-surface area, not colour | Validated for repigmented area or extent, not ΔE | Mixed research/proprietary implementations |

---

## Appendix 1. Quote check of the priority numbers (checking thread, 2026-11-28)

Standard: `.claude/agents/verifier.md`, applied to the report's numbers instead of a staging record. A number is FOUND only if the string is in a source text this thread read. Sources read:

- Wang et al. 2018, *Color Res Appl*, doi 10.1002/col.22230: FULL_TEXT, CC BY open-access copy from the White Rose eprints repository (record 128275). Wiley's own page returned HTTP 403.
- Cronin et al. 2023, *J Biophotonics*, doi 10.1002/jbio.202200381: FULL_TEXT from PMC (PMC10247498, NCBI efetch).
- Matias et al. 2015 (PMID 25645051), Vander Haeghen & Naeyaert 2006 (PMID 16415385), Navarro et al. 2019 (PMID 29993849): ABSTRACT_ONLY from PubMed. Vander Haeghen: jamanetwork.com returned HTTP 403 to the article page and to the free PDF link (two attempts). Navarro: the author-repository preprint at repositorio.uam.es returned HTTP 403 twice. Matias: closed access, not attempted at the publisher.
- Konica Minolta CM-700d product page (sensing.konicaminolta.us), SpectraMagic NX2 manual v1.2 (PDF from the same site), and the SPW Industrial listing: read 2026-11-28.

| # | Report claim | Source checked | Result | What the source says |
|---|---|---|---|---|
| 1 | CM-700d small aperture mean MCDM “0.39” ΔE\*ab (exec. summary calls it “without repositioning”) | Wang, Table 1 and text | **FOUND with differences** | Table 1, human skin, column SA: Mean 0.39. Text: “the mean MCDM values for the MA and SA aperture sizes were 0.35 and 0.39”. 0.39 is the small-aperture mean, not the no-repositioning figure. The no-repositioning (continuous, CT) mean is 0.37. |
| 2 | “0.63” with consecutive replacement; continuous “0.37” | Wang, Table 1 and text | **FOUND verbatim** | “continuous repeatability (CT) is much better than consecutive repeatability (CS) by almost a factor of 2 (0.63 vs. 0.37 DEab)”. Table 1 max for CS is 1.82. |
| 3 | Large aperture “0.35”; best configuration “0.34” | Wang, text | **FOUND** | “The smallest variability was found for the large aperture size and low-pressure mask, 0.34 DEab”. |
| 4 | Aperture change “2.48” or “3.04”; pressure change at small aperture “1.82” | Wang, Table 2 | **FOUND verbatim** | Table 2: “SAV with different pressure: HP and LP 1.82”; “LP with different aperture size: MA and SA 2.48”; “HP … 3.04”. |
| 5 | Wang context (not stated in the report) | Wang, methods | note | 11 subjects, forehead and cheekbone only, a 3 mm aperture is the smallest tested. Abstract: “The differences between the measurements for different body locations were, in general, larger than the instrument repeatability”. Nothing measured a small lesion. |
| 6 | CM-700d “8/11 mm” MAV, “3/6 mm” SAV | KM product page | **FOUND with differences** (formatting only) | “MAV: Φ8 mm/ Φ11 mm SAV: Φ3 mm/ Φ6 mm”. |
| 7 | White-tile repeatability “ΔE\*ab 0.04”, inter-instrument “ΔE\*ab 0.2” | KM product page | **FOUND** | “Standard deviation within ΔE\*ab 0.04 \* When a white calibration plate is measured 30 x at 10-second intervals”; “Inter-instrument agreement Within ΔE\*ab 0.2 (MAV/SCI)”. The 0.2 applies to the large aperture only. |
| 8 | CM-700d-U “USAV (2.4mm)” | SpectraMagic NX2 manual | **FOUND verbatim** | “CM-700d-U USAV (2.4mm) (Unchangeable)”. No skin validation was looked for beyond the report's claim. |
| 9 | CM-700d price “$6,749.93” | SPW Industrial listing | **FOUND verbatim** | “$6,749.93”, a reseller listing with software and accessories, not a manufacturer price. |
| 10 | Antera CV “0.36%” L\*, “1.56%” a\*, “0.58%” b\*; CL 400 “0.66%”, “3.06%”, “2.01%” | Matias abstract | **NOT CHECKABLE** (paywall; not in abstract) | Abstract gives no numbers. It supports only the direction: “Repeatability of Mexameter® MX-18 and Colorimeter® CL-400 values were lower than that of Antera 3D® for all the parameters analysed.” 30 volunteers, UVB-exposed skin. |
| 11 | Whole-process “3.7” mean, “10.4” 99th percentile; “0.4”/“1.2”; “5.1”/“15.4”; “1.5”/“2.9”; threshold “>10” ΔE\*ab | Vander Haeghen abstract | **NOT CHECKABLE** (publisher HTTP 403 twice; not in abstract) | Abstract gives no numbers: “calibrated images exhibit markedly improved precision and accuracy compared with noncalibrated images, all variability of the imaging process cannot be eliminated.” Abstract says accuracy was assessed on “images of color squares”, so whether any figure is skin is unknown. The report's claim that within-image lesion/background comparisons were more stable is also not in the abstract. |
| 12 | Navarro: “10” lesions, mean error “0.23 mm” in diameter evolution; worse with longer intervals | Navarro abstract | **NOT CHECKABLE** (repository HTTP 403 twice; not in abstract) | Abstract mentions an image registration approach and “a case study with the lesion-size feature”; no lesion count, no error figure, nothing on interval. PMID and DOI match the paper. |
| 13 | Cronin: angle altered L\*, a\*, b\*; distance altered L\*; “standard errors exceeding 1 CIELAB unit”; DNG less variable than JPEG | Cronin full text | **FOUND with differences** | “distance only affected L\* (standard error of measurement, SEM > 1 CIELAB unit)”; “raw (DNG) images had decreased median variability”. The report omits that the targets were Pantone Skintone Guide swatches, not skin, that “only the lightness channel in the parallel (‖) angle experiment had SEMs greater than 5 LAB units”, and that “Flash usage did not generally reduce distance and angle associated variability.” |

Extra numbers checked against PubMed abstracts in the same pass (not priorities):

| Report claim | Result |
|---|---|
| Niakan (PMID 39627966): 7.59, 7.65, 3.79, 3.70, 1.34, 0.96 ΔE00, MiniScan, forehead | **FOUND**, all six numbers in the abstract. |
| DIAS (PMID 22621363): 21 patches, ICC 0.83 | **FOUND with differences**: “One vitiligo patch was selected in each patient (n = 21)” after punch grafting; ICC 0.83 is “agreement between the three clinical observers and the DIAS”. |
| Computerized DIAS (PMID 25367709): κ 0.17 | **FOUND**: “The κ test of consistency was 0.17 (P = 0.053)”. 6 and 24 weeks also in the abstract. |
| Pigmentation area (PMID 26705766): 92.1%, SD 4.6% | **FOUND**: “mean accuracy of 92.1% and a standard deviation of 4.6%”. |
| VES (PMID 26827762): ICC 0.943, 0.904, SDC95 1.31% and 1.85% | **not in abstract**. The abstract's ICCs are different figures (“VES: 0.924 vs. Vitiligo Area Scoring Index: 0.846”, live interrater). Full text needed. |
| Smeaton (PMID 32726869): 0.628, 0.860, −0.421 | **not in abstract**. Full text needed. |
| Multispectral prototype (PMID 32578406): ΔL\* ≈ 3, Δa\* ≈ 3, BOM < $40 | **not in abstract**. Full text needed (PMC7309634 exists; not read). |

**Tally of the priority numbers.** 12 numeric claims (row 5 is a context note, not a claim): 9 FOUND (6 exact, 3 with differences, of which row 1 changes the meaning), 3 NOT CHECKABLE (rows 10 to 12), 0 DOES NOT MATCH. Extra pass: 7 claims, 4 FOUND, 3 not in abstract. Every PMID and DOI checked resolves to the paper the report names.

## Appendix 2. Comparison with the measurement plan (checking thread's judgment, not the report's)

Everything in this appendix is **[judgment]**. It compares the report with `content/measurement-tool-plan.md` on main and with the kit in its Appendix A (PR 13, not merged). The plan is not edited here. Only numbers marked FOUND in Appendix 1 are used.

### What the checked findings support

1. **Photography, not a contact instrument, for a 2 mm spot.** The smallest skin-tested contact aperture is 3 mm (Wang), already larger than a 2 mm spot, so it would read surrounding skin with the spot. The 2.4 mm aperture exists only in the manual, untested on skin. Wang found that changing the measured area changed the reading by 2.48 to 3.04 ΔE\*ab. That is a contact-instrument effect, but it backs the plan's fixed-radius disc (section 4.4): the disc size must never change between sessions.
2. **A within-image spot-minus-ring endpoint.** Wang found differences between body sites were "in general, larger than the instrument repeatability". Skin varies from place to place more than instruments do, so comparing the spot with its own surrounding ring in the same image is the right measure. This is the plan's measurand (section 2.1). The report's stronger claim that Vander Haeghen showed within-image comparisons to be more stable is NOT CHECKABLE.
3. **Raw capture** (plan C5, kit body choice). Cronin: raw files had lower median variability than the phone's processed JPEGs.
4. **A study-specific SDC from repeated full captures with repositioning** (plan section 2.2 and rung 2). The report reaches the same conclusion, and Wang's numbers show why: lifting and replacing the instrument nearly doubled the variability, from 0.37 to 0.63 ΔE\*ab, with a worst case of 1.82. Only a repeat that includes repositioning gives an honest figure.

### What puts pressure on the plan

5. **The 1.0 L\* target at 2 mm is ambitious, and no source shows it reached.** No method in the report has a longitudinal SDC. The best contact-instrument figure, on smooth facial skin with repositioning, is a mean of 0.63 ΔE\*ab between readings in one session. Only as a rough guide: if a per-reading error of that size were the standard error of measurement, the plan's formula (SDC = 1.96 × √2 × SEM) would give [about 1.7]. The plan's measure is a difference within one image, which cancels much of the shared error, so the target is not contradicted. It is also not supported by anything outside our own simulations. The phantom rung (rung 2) decides it. If the measured SDC comes out between 1 and 2, the plan should say so rather than move the target quietly.
6. **Angle is a large error source.** Cronin: tilting the camera raised L\* error above 5 units in one experiment, against about 1 unit for distance. Plan C6 checks perpendicularity only after the fact, from the card's shape. The kit appendix leaves a rigid spacer as "can be added later". These figures argue for having it from day one.
7. **The ring flash is not proven by this evidence.** Cronin found a phone's flash "did not generally reduce" variability. A phone flash is not a cross-polarised ring flash, so this does not argue against the kit, but the kit's lighting is one more thing the phantom tests have to show works.

### Numbers Ben should not rely on (NOT CHECKABLE or not in abstract)

- Vander Haeghen & Naeyaert: 3.7 / 10.4 whole-process error, the "> 10 ΔE\*ab" significance threshold, and every other number in section 4. These would be the most damaging if true: they would mean absolute colour from calibrated photos is far too noisy for a 1.0 target. They are not usable until a PDF is read.
- Matias: all Antera and CL 400 coefficients of variation.
- Navarro: "10" lesions and "0.23 mm". This would be the key figure for the plan's registration problem (section 4), so it is worth getting the paper.
- VES 0.943 / 1.31%, Smeaton correlations, multispectral prototype ΔL\* ≈ 3 and < $40.
- The report's summary sentence calling 0.39 "without repositioning". The no-repositioning figure is 0.37; 0.39 is the small-aperture figure.

### Proposed changes for Ben

Update 2026-11-28 02:10 UTC: Ben said "you are good to make teh changes you think ar eright" (02:04 UTC). The changes to sections 2.3, 3 (C6 and a kit note) and 7 were made in `content/measurement-tool-plan.md` on this branch. Appendix A (PR 13) still says the spacer can come later. That line should change when PR 13 is merged.

- **Kit, before buying:** no change to the camera body, lens, flash, polariser or card. Nothing checked argues against them, and the checked findings (raw capture, a fixed disc, a within-image endpoint, a contact aperture too big for a 2 mm spot) support the camera route. **Add one item:** a rigid spacer or small copy stand that fixes both distance and angle. Make it part of the kit now instead of "later" (it is cheap; not priced).
- **Kit, do not add:** a Konica Minolta CM-700d (about $6,750 at a reseller) as the main instrument. Its skin-tested aperture is larger than the target spot. Borrowing one for a single session to anchor phantom and card colours (plan open question 4) is still worth doing.
- **Plan section 2.3:** add one sentence saying that no published method found reports an L\* or ΔE smallest detectable change over time for spots this small, so the 1.0 target is the project's own design target, to be confirmed or revised at rung 2.
- **Plan section 3, C6:** change "checked by the card's shape" to "fixed by the spacer and checked by the card's shape", citing Cronin's angle result.
- **Plan section 7 (prior art):** add Wang 2018 (open access, checked) as the contact-instrument baseline. List Vander Haeghen 2006 and Navarro 2019 as PDFs to obtain (both on the paywall list in `STATUS.md`).
