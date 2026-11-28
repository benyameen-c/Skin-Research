# Review: free photo method papers for the measurement plan

## About this page

Written 2026-11-28 for `content/measurement-tool-plan.md` sections 3, 4 and 7. It reads in full the 13 leads in `data/lineup_search_candidates.csv` that had a free copy listed by Europe PMC (Ben's go-ahead, 02:40 UTC 2026-11-28). These are measurement method papers, not treatment studies, so nothing here enters `data/evidence.csv`.

- **Sources.** 11 papers were read as full-text XML from Europe PMC (`/europepmc/webservices/rest/<PMCID>/fullTextXML`; 3 of them returned HTTP 500 there and were then read from the same PMC record through NCBI efetch). The 2 JAMA Dermatology consensus papers were read as the final published PDFs deposited in the University of Arizona repository (handles 10150/623192 and 10150/624154), the free link Europe PMC lists. Plain text of each is saved in the project files at `papers/excerpts/<file>` (file names below); the two PDFs are in `papers/pdfs/photo-methods/`. None of this is committed. No source was paywalled, so nothing was added to the paywall list.
- **Quotes.** Every reported result (error, repeatability, agreement, sample size) sits in a verbatim quote in straight double quotes, taken from the saved text of the paper named in the same section. `tools/photo_methods_check.py` checks each quote against that file (129 quotes, 0 fails on 2026-11-28). Our own arithmetic, such as the area of a 2 mm spot, is in [square brackets].
- **Units.** Several papers report pixels, ICCs or card-patch ΔE rather than L\* on skin. Where a paper gives no figure in the plan's units, that is said in words; no paper's pixel or ICC figure is converted into mm or L\* units.
- **Scope.** Lesion sizes and types are as tested by each paper. None of the 13 tested IGH spots, and none tested a lesion as small as 2 mm for colour repeatability.

## Summary table

What each paper offers the plan, in one line. *Repeat* means the paper photographed the same thing again and reports the spread; *accuracy* means one capture compared with a reference.

| # | Paper | Kind of method | Best figure it gives | Tested on | Says anything at 2 mm? |
|---|---|---|---|---|---|
| 1 | Nevus follow-up 2022 | side-by-side reading of two visits; 2D vs 3D diameter | count SD between readers, diameter ICC | torso nevi, at least 4 mm for diameters | no; light lesions fail |
| 2 | Polarimetric registration 2022 | keypoint (KAZE) registration within one session | matching pairs only, no error in mm | phantom, 2 mm honey drop, one nevus | yes, a 2 mm target, but within one session and no error figure |
| 3 | Mpox hand alignment 2025 | rigid plus learned deformable registration between visits | lesion-centre error in pixels | mpox on hands | no mm scale |
| 4 | Face-alignment app 2024 | live overlay that releases the shutter at the right framing | repeat L\* CV against a colorimeter | 8 mm stickers on faces | no; 8 mm |
| 5 | Rater reliability 2013 | card-corrected photos read twice by two analysts | ICCs, no L\* units | normal skin, large areas | no; small areas did worse |
| 6 | Psoriasis erythema 2016 | linear card correction | red-channel SD across cameras, 18 to 10 | plaques, one normal elbow | no |
| 7 | Two face imagers 2026 | per-image second-order card correction | card ΔE drift over 4 weeks, under 1 after correction | card patches | no skin figures |
| 8 | Dermoscope lights 2022 | spectra and card photos under 7 lights | ΔE 3 to 8 between two LED dermoscopes | card, one nevus | no |
| 9 | Cameras and lights 2025 | single-capture card accuracy, 6 devices | average ΔE\* per device (non-standard scale) | card | no |
| 10 | ISIC consensus 2017 | expert Delphi | none | none | no |
| 11 | ISIC guidelines 2017 | practical guide | none | none | no |
| 12 | UV photography 2020 | UV camera plus traced area, repeat photos | area limits of agreement in cm² | vitiligo, flat skin | too coarse for a 2 mm spot |
| 13 | AI vitiligo extent 2026 | UNet segmentation plus lesion-vs-nearby-skin contrast | ICC with physicians | facial vitiligo | no |

None of the 13 reports a between-visit L\* repeatability on skin, so the plan's statement in 2.3 that no published method gives a longitudinal smallest detectable change at this size still stands after this reading.

## 1. Longitudinal nevus evaluation from clinical images (PMID 34455638)

Skin Res Technol 2022, doi:10.1111/srt.13092, PMC9907704, CC BY-NC-ND. Source file `pmc_9907704.txt`.

- **Method.** Not image registration in software. It compares two reading protocols: counting nevi on each time point's photos separately ("method I") against comparing the two time points side by side ("method II"), and manual 2D diameters in ImageJ against automated 3D (VECTRA) diameters.
- **Figures.** Count spread between 4 readers: "The standard deviation was greater in method I (38.80) than in method II (4.65) (p = 0.0025)." Diameter agreement: "intraclass correlation coefficient (ICC) = 0.88 (95% CI [0.77, 0.93])". Manual against automated: "The observed mean percent difference between manual and automated measurements was 1.5% (95% CI [−0.5%, 3.8%])", but for the hard cases "The estimated manual diameters of these moles were 37.4% larger than their automated diameters."
- **Tested on.** Pigmented nevi on the torso, "nevi at least 4 mm in diameter" for the 2D against 3D comparison; "a total of 184 nevi on the torso of 5 patients". Readers were "four fourth‐year medical students".
- **Limits.** The two failures are the ones that matter for a white spot: "Nevi that were lightly pigmented or at the lateral edge of the torso had lower agreement", and "The main limitation for 2D manual measurement is curvature of body sites". No colour measurement. The authors list "the small numbers of participants".
- **Use for us.** The paired, side-by-side reading of two visits beats reading each visit alone. Low-contrast lesions and curved skin are where automated segmentation fails.

## 2. Registration of polarimetric skin images (PMID 36042549)

J Biomed Opt 2022, doi:10.1117/1.JBO.27.9.096001, PMC9424913, CC BY. Source file `pmc_9424913.txt`.

- **Method.** Registers the 36 images of one Mueller-matrix acquisition (seconds apart, same session) to each other. Keypoint features (KAZE detector and descriptor), outliers removed by MSAC, then a geometric transform; if too few matches, the operator clicks control points by hand. Compared with plain intensity-based registration.
- **Figures.** Matching pairs found between two raw images with KAZE: 1067 on a nevus and 873 on "Honey drop on healthy skin" (Table 2, row "KAZE | KAZE | 9210 | 3668 | 1067 | 6616 | 3785 | 873"). On a printed phantom moved during capture, retardance at the centre was "Still | 0.8680", unaligned "Unaligned | 2.2888", feature-based "Alignment (a) | 0.9077" and intensity-based "Alignment (b) | 2.1826" (Table 3). No registration error in pixels or mm is reported.
- **Tested on.** A printed lesion phantom, a honey drop on hairy arm skin ("The diameter of the honey drop is ∼2 mm"), and one benign nevus.
- **Limits.** Within one session only, not between visits. The authors warn that skin "rarely shows sufficient key points with strong contrast (except for mole evaluation", and that "Due to the lack of matching points in skin images, feature matching is not a reliable method for batch image processing alone." They also note that "the visibility of features in human skin can depend on the combination of the state of the polarization state generator and the PSA", which matters for a cross-polarised kit.
- **Use for us.** Keypoint registration with a fitted geometric transform did recover a 2 mm target on hairy arm skin where intensity registration did not, but the paper gives only qualitative proof and keeps a manual fallback.

## 3. Deep alignment of mpox hand photographs (PMID 40822979)

Proc IEEE ISBI 2025, doi:10.1109/isbi60581.2025.10981147, PMC12352120 (NIH manuscript). Source file `pmc_12352120.txt`.

- **Method.** Two steps between visits: hand key points (MediaPipe, 21 per hand) and a Procrustes "rigid body and scaling transformation" onto a template, then a learned deformable registration (VoxelMorph, UNet, normalised cross-correlation loss with a smoothness penalty).
- **Figures.** Mean pixel error on 1024 × 1024 crops (Table 1). Lesion centres: "Lesion Center Mean Error (pix) | 29.43 ±13.86 | 28.89 ±13.50 | 29.08 ±13.91 | 28.98 ±14.02" (baseline rigid, then three regularisation strengths). Hand key points: "21 Keypts Mean Error (pix) | 19.05 ±7.23 | 18.57 ±7.37 | 17.87 ±6.27 | 16.22 ±6.02". Per pair: "In 115 out of 127 samples (90.6%), VoxelMorph reduced the registration error by a small margin." The paper gives no pixels-per-mm, so these errors cannot be put in mm.
- **Tested on.** Mpox lesions on hands, "a unique dataset of 1,658 hand images" for training and "a test set of 254 images", taken with "an Apple iPhone 12 Pro camera" in a field trial.
- **Limits.** Lesion centres improved less than anatomical key points, "likely due to the random distribution of lesions and their variable appearance over time". Fingers and gaps between them cause trouble ("regions with intense spatial discontinuities, such as interdigital areas"). Error fell when there were more lesions: "We speculate that a higher number of lesions may act as anchor points for alignment."
- **Use for us.** The lesions that changed between visits registered worse than the stable anatomy, the same trap the plan names in 4.2 (registering on the spot moves the registration with the spot). Other spots near the target can act as anchors.

## 4. Smartphone app with face alignment indicators (PMID 38978223)

Skin Res Technol 2024, doi:10.1111/srt.13824, PMC11230921, CC BY. Source file `pmc_11230921.txt`.

- **Method.** Repositioning at capture, not registration afterwards. The app overlays a target drawn from facial landmarks of a first "criterion image" and fires the shutter only when the live face matches it within a tolerance k ("The constant k takes values of 0.05 or 0.025 in this study"). Room dark ("ambient light is 0lx"), phone screen as the light source, sRGB JPEG output. Colour measured on stickers stuck to the face.
- **Figures.** Reference instrument on the cyan sticker: "56.060 ± 0.082" L\* (colorimeter, "n = 25"). Spread of L\* across repeat app captures, as a coefficient of variation: "Hand/Tol. | 0.045341" against "Control | 0.003042" for the colorimeter (Table 1), which the abstract reports as "CVs of 14.9 times, 8.14 times, and 4.41 times for L*, a*, and b*". Smallest difference it resolved between skin and an 8 mm skin-coloured patch: "the smallest color difference ∆Eab of 1.901"; for lightness, "The smallest ∆L* value was recorded between patch1 and patch2 (∆L* = 2.150)".
- **Tested on.** Faces of "eight participants" and a mannequin; colour targets were "8‐mm in diameter" stickers.
- **Limits.** The method is "not absolute quantification but relative quantification". JPEG in sRGB, so tone processing was not removed. The authors' own lesson: "the L* value is most sensitive to changes in camera‐object distance". The "detection limit" is the smallest difference that happened to be significant in one participant with "n = 5" images, not a smallest detectable change from repeat sessions. The text and Table 1 disagree on which condition had the smallest CVs.
- **Use for us.** A live overlay that releases the shutter only when the framing matches the first visit is cheap and works for repositioning. Even so, L\* spread was several times an instrument's, and the authors blame camera distance. Cronin 2023 (plan C6) found angle mattered more than distance in its setup. Either way, the rigid spacer that fixes both is the answer.

## 5. Rater reliability of skin colour from calibrated photos (PMID 23551208)

Skin Res Technol 2013, doi:10.1111/srt.12072, PMC3778111 (NIH manuscript). Source file `pmc_3778111.txt`.

- **Method.** Colour-card correction per participant folder (Munsell ColorChecker mini card, Pictocolor plug-in), then L\*a\*b\* read in Photoshop either with a lasso over a large patch or with the eyedropper set to "‘5 × 5 Average’ pixel sample size (total of 25 pixels)", repeated 3 or 9 times. Images were uncompressed TIFF from a colposcope camera.
- **Figures.** Same images read again by the same and a second analyst; one-way ICCs. Within a rater, lasso on skin: "(ICC ≥ 0.99)"; small-area sampler: "ICC = 0.91 for expert, ICC = 0.81 for novice". Between raters, skin: "L* | 0.98 | 0.93 | 0.83" and "a* | 0.76 | 0.83 | 0.82" (skin, labia, vaginal wall; Table 2). No figure in L\* units is given.
- **Tested on.** Normal skin at five sites plus mucosa, "210 randomly ordered images" (10 folders, each repeated 3 times). Lasso areas were "120,000–150,000 pixels".
- **Limits.** This is reliability of reading the same image, not of re-imaging. Folders were chosen by the expert "based on clarity and representativeness of skin color; no random assignment was used." Small sampled areas agreed less: "Lower agreement in the color sampler technique (25 pixels) as compared with the lasso technique (120,000–150,000 pixels) suggests that, for small areas of skin color analysis, additional training may be required."
- **A trap worth knowing.** Photoshop's lasso histogram is not L\*: "the 0–100 range of L* values has been scaled by Adobe Photoshop® into 256 levels", so they used "[L* value mean = (Adobe Photoshop® histogram mean) (100)/255]" and subtracted 128 from a\* and b\*. Any tool that reads 8-bit Lab must undo this.
- **Use for us.** A 2 mm disc at the plan's 20 px/mm holds [about 1,250 pixels, π × 20² for a 1 mm radius], two orders of magnitude fewer than their lasso area. Their result says small regions are where reading error grows, so the plan should measure reading error on the actual disc size, not borrow large-patch figures.

## 6. Erythema from colour-card-calibrated photos (PMID 26517973)

Skin Res Technol 2016, doi:10.1111/srt.12276, PMC4851905 (NIH manuscript). Source file `pmc_4851905.txt`.

- **Method.** A 24-patch card in every frame; "computing a linear color transform that minimizes the mean square error between the color values detected in the image and the reference color values", applied to the whole image. A person then drew a box on the plaque and one on normal skin; features fed a classifier of the dermatologists' 0 to 4 erythema score.
- **Figures.** Agreement with the panel: "The color calibration process improved the agreement from κ = 0.2364 to κ = 0.4203." Across six cameras photographing one normal elbow five times each, the spread of the mean red channel fell with calibration: "the standard deviation of the average red channel value of the calibrated images (s = 10) is significantly less than the standard deviation of the averaged red channel value of the uncalibrated images (s = 18) (p=0.0008)". No L\* figure.
- **Tested on.** Psoriasis plaques on knees and elbows, "20 patients", "a total of 80 images", under "The normal lighting of the clinic rooms".
- **Limits.** A card corrects only what lights the card: "the shadow was over the plaque but not on the color card because the color calibration could not account for the shadows." Room lighting, two consumer cameras, and a field of view wide enough for the card meant less detail on the plaque: "the larger field of view needed to include the color card in the images can also make classification more challenging".
- **Use for us.** A card cut the camera-to-camera spread of the red channel [by roughly half, 18 to 10], and the failure was uneven light, which no card can fix. This supports plan C3 (device light only) and the open task T1 (lighting gradients).

## 7. Colour calibration of two full-face imaging devices (PMID 41766450)

Int J Cosmet Sci 2026, doi:10.1111/ics.70090, PMC13636185, CC BY. Source file `pmc_13636185.txt`.

- **Method.** The same card as the PR 13 kit, "The X‐Rite ColorChecker® Classic‐Nano, which measures 24 × 40 mm", fixed in the field of view of two commercial face imagers (one diffuse xenon, one cross-polarised LED). Per image, "A second‐order polynomial model" maps camera RGB to the card's D65 reference values. Stability is ΔE between visits measured on the card patches.
- **Figures.** Card ΔE from week 0 to week 4, before and after calibration. Cross-polarised LED device: "the mean ΔE (T4w vs. T0) significantly decreased from 2.50 to 0.93". Diffuse xenon device: "a mean ΔE (T4w vs. T0) of about 0.67" before, and after calibration "a post‐calibration colour difference between time points of less than 0.5". Study: "six healthy Chinese female subjects", "bi‐weekly measurements".
- **Tested on.** Card patches in full-face images. Although the stated aim includes skin tone, the results report only card patches; no skin L\* repeatability is given.
- **Limits.** Six people, one ethnicity, four weeks, no skin-region figures, and no per-patch table in the text (Figures 3 and 4 only). The authors' guess at the LED device's drift: "may relate to the flash mode in the operation, although the LED light source does not typically experience significant attenuation, they may not achieve a steady state instantaneously."
- **Use for us.** The nearest published thing to our drift question: with the same card in frame, a per-image second-order polynomial brought four-week drift of the card itself under 1 ΔE on both devices. That is an upper bound on what card correction can remove; it says nothing about skin placement or a 2 mm spot.

## 8. Dermoscope light sources and reflected colour (PMID 36452032)

J Biomed Opt 2022, doi:10.1117/1.JBO.27.8.080902, PMC9360608, CC BY. Source file `pmc_9360608.txt`.

- **Method.** A review with a small experiment. A spectrometer measured the spectrum of four dermoscopes, an iPhone LED, a xenon flash and daylight; a micro ColorChecker was photographed in DNG through each with "the same exposure settings".
- **Figures.** Between two common LED dermoscopes after white balance: "For the color “light skin,” dermoscope #3 compared with dermoscope #4 showed ΔE=3", "For the color “blue sky,” ΔE=6", "For the color “orange-yellow,” ΔE=8". On a real nevus: "when L*a*b* values of the same region in both images were compared, ΔE=14.5." (one point measurement, no repeats).
- **Tested on.** A card and one dermal nevus.
- **Limits.** No repeat measurements, no uncertainty, and the authors say the nevus comparison "is somewhat limited by the lack of a “ground-truth” measurement". The ΔE thresholds it cites (1 noticeable, "between two and four in the field of dentistry") are borrowed, not measured on skin.
- **Use for us.** Different LED sources render the same surface differently even after white balance: "a significant degree of difference persists even in the context of white balance correction." So the light source must never change over the study, and a card corrects a light source only partly. Halogen and xenon had the broadest spectra; white LEDs show "the characteristic narrow spike in the blue region".

## 9. Colour accuracy across cameras and lights (PMID 40278023)

J Imaging 2025, doi:10.3390/jimaging11040107, PMC12027704, CC BY. Source file `pmc_12027704.txt`.

- **Method.** Single captures of a 24-patch ColorChecker with six devices (two Canon cameras, a Sony, two phones and a clinical video dermoscope), under a studio LED and under dermoscope LEDs; patches found with MATLAB `colorChecker` and ΔE computed against the reference values. Spectra and CRI/TLCI of each light measured. Also a manual phone setting derived from a grey card.
- **Figures.** Average ΔE\* over 24 patches under the studio light: Canon EOS R7 "Aver. | 11.5", iPhone 13 "Aver. | 18" (Table 2); under dermoscope light the iPhone's average was "ΔE* = 26.5". Light quality: "The DermLite DL4 LED exhibited significantly lower performance, with a CRI of 84.50 and a TLCI of 61.10", while the studio LED had "a CRI of 96.41 and a TLCI of 97.47".
- **Tested on.** A card only; clinical images of moles and melanomas were compared by eye.
- **Limits.** These are accuracy errors of single captures, not repeatability; the images were saved "without additional processing", so no card-based colour correction sits behind the Table 2 figures. Their ΔE is not standard either: they report "standardizing the coordinate values", "resulting in dimensionless quantities for ΔE*, ΔC*, and ΔL*", so the numbers cannot be compared with other papers. The authors: "our results did not demonstrate an absolute correlation between the ΔE values of individual color samples in the image and those obtained from the CRI and TLCI charts."
- **Use for us.** Auto mode is the enemy; fixed manual white balance, ISO and shutter matched to the light helped the phone images ("automatic mode (Figure 8c) may compromise critical visual information"). This backs plan C5 (locked settings, raw). The absolute errors here do not size our noise, because our measurand is a within-frame difference after card correction.

## 10. ISIC Delphi consensus on imaging technique (PMID 27892996)

JAMA Dermatol 2017;153(2):207-213, doi:10.1001/jamadermatol.2016.3949, final published PDF in the University of Arizona repository. Source file `katragadda2017.txt`.

- **Method.** Expert consensus, not measurement: a Delphi process across 5 rounds that ended with "an EG set of 33 recommendations". An item was kept "if both mean and median rating was 4 or higher".
- **Figures.** None on error or repeatability.
- **What it recommends that bears on us.** Consistency over visits: "the camera should follow a similar orientation as the one obtained in previous imaging sessions." Geometry: "the camera should be oriented perpendicular to the skin surface." Centring: "the lesion should be balanced and centered in the field of view, while attempting to capture an equal area of healthy skin surrounding the lesion." Light: "Relative to the skin surface, and whenever possible, the lighting source should be on an angle or oblique to the skin being photographed." Colour: "Imaging parameters should permit color comparisons between images and over time." Storage: "JPG (minimally compressed), TIFF, PNG (lossless), and RAW."
- **Limits.** Opinions of a panel weighted towards melanoma imaging. The authors call for "Feasibility and validity testing under real-world clinical conditions". The scale direction is printed both ways ("1 (strongly agree) to 5 (strongly disagree)" in the abstract, "1 (strongly disagree) to 5 (strongly agree)" in the Methods). They flag what was not settled: "It may also be helpful to consider procedures to assure that the camera is indeed perpendicular to the skin surface".
- **Use for us.** The plan already meets the perpendicular, centred, consistent-orientation and raw-storage items. The oblique-light item conflicts with an on-axis ring flash; for a measurement (not a clinical photo) cross-polarisation is the plan's answer to glare, so this is a choice to state, not a rule to follow.

## 11. ISIC practical guidelines for clinical images (PMID 28241182)

JAMA Dermatol 2017;153(5):453-457, doi:10.1001/jamadermatol.2016.6214, final published PDF in the University of Arizona repository. Source file `finnane2017.txt`.

- **Method.** A clinical photographer tried the 33 consensus items in practice and supplied example images. No measurement.
- **Figures.** One practical rule of thumb: resolution "generally equates to a joint photographic expert group (JPEG) file at least 200KB in size."
- **What bears on us.** Why repeat geometry matters: "if 2 images are taken of a lesion 6 months apart in a different pose and lighting, this can completely preclude the ability to identify changes in the lesion over time." Why a fixed distance matters: "For digital camera photography the object distance is not fixed but dependent on how far the photographer holds the camera from the skin lesion. Hence, a linear measurement cannot be geometrically calculated." Lighting advice for clinical photos: "avoiding the use of a flash, and positioning the light source oblique to the skin surface".
- **Limits.** Written for documentation and teledermatology, not colour measurement. No test of whether following the advice reduces error.
- **Use for us.** The six-month sentence is the plan's own problem stated by the field's standards group. The no-flash advice is aimed at uncontrolled direct flash; the PR 13 kit's cross-polarised ring flash is a deliberate departure that the plan should name and justify (glare control, fixed output), and rung 2 should test.

## 12. UV photography for vitiligo lesion area (PMID 31994253)

J Eur Acad Dermatol Venereol 2020, doi:10.1111/jdv.16226, PMC7496888, CC BY-NC. Source file `pmc_7496888.txt`.

- **Method.** A converted camera with its UV/IR filter removed, "A 20‐nm narrow‐band filter was used transmitting UV light around 365 nm", two UV softboxes, and "A 0.75 inch size sticker was applied next to the selected lesions as a reference". Area traced in ImageJ and compared with a normal camera under Wood's lamps, tracings on transparent sheets and graph paper.
- **Figures.** Agreement with the other methods: "0.984, 0.988 and 0.983, respectively". Repeat photos: "The ICC for the intra‐rater reliability was 0.999" and "the ICC for the inter‐rater reliability was 0.998". In area units: "The mean difference in the intra‐rater reliability was 0.04 cm2 with limits of agreement of 0.35 and −0.28 cm2."
- **Tested on.** Vitiligo: "31 target lesions of 17 consecutively screened patients", "Fitzpatrick skin types 1–4", lesions on "a flat surface". Lesion sizes are not reported in the text.
- **Limits.** Area only, no colour. "UV photography cannot be used for assessment of lesions which are localized on curved skin". The authors add that "these correlations do not implicate exact agreement".
- **Use for us.** This is the only paper of the 13 with repeat photos of a white lesion and an error in physical units. Those limits of agreement are [about ten times] the whole area of a 2 mm spot [π × 0.1² = 0.031 cm²], so the method as tested is far too coarse for A(t) at our size. Whether IGH spots show the same UV contrast as vitiligo is an open question this paper does not answer.

## 13. AI measurement of vitiligo depigmentation extent (PMID 42081176)

Dermatol Ther (Heidelb) 2026, doi:10.1007/s13555-026-01736-8, PMC13237307, CC BY-NC. Source file `pmc_13237307.txt`. Funded by and written by employees of Pfizer.

- **Method.** A UNet segments depigmented skin in cross-polarised clinical-trial face photos. Colour contrast: an index (IWANewtone) per pixel from CIELAB, averaged over the lesion, against "the median of the IWANewtone from the pixels in neighboring unaffected regions". Digital F-VASI is extent times that difference.
- **Figures.** Validation on held-out people: segmentation "the optimal model reached a coefficient of 81% in the validation dataset"; extent against physicians "the interclass correlation coefficient between computationally calculated and physician-assessed extent of facial vitiligo was 0.81"; score against physicians "The digital VASI and physician-assessed F-VASI showed an interclass correlation coefficient of 0.91". Data: "facial images of 85 participants for model training" and "the 21 participants who were independent of the training set".
- **Tested on.** Facial nonsegmental vitiligo, large patches, Canfield total-body photography from a phase 2b trial (NCT03715829).
- **Limits.** The abstract calls the 0.81 "81% accuracy", while the Methods define it as an intraclass correlation, so read it as an ICC. Agreement is with human scores, not with any physical truth, and there is no repeat-visit reliability. The authors: "the digital VASI algorithm’s performance in real-world imaging conditions (e.g., non-standardized variable lighting, smartphone cameras) remains to be evaluated."
- **Use for us.** Independent support for the plan's contrast design (spot against nearby unaffected skin). It adds nothing on small-spot repeatability.

## What these papers suggest for the plan and the simulations (my reading)

This section is my judgment, not a finding of any paper. Nothing here has been applied; `content/measurement-tool-plan.md` is unchanged. Section numbers in brackets point to the papers above.

**Headline.** The 13 papers support the plan's design (fixed light, card in frame, locked raw capture, perpendicular camera, contrast against nearby skin) more than they change it. None gives a number that could replace the plan's own 1.0 L\* target, and none measured repeat-visit colour on anything as small as 2 mm. The useful additions are about rotation and scale in registration, the light source, and the card-correction model.

### Measurement plan

1. **C3, light source.** Add: one light source for the whole study, never swapped or upgraded mid-study, with its spectrum or at least colour temperature recorded once. Different white LEDs render the same patch differently even after white balance [8, 9]. Before buying, check whether the PR 13 ring flash is a xenon tube or LED; broad-spectrum sources rendered colour best in [8, 9]. Not checked here.
2. **C4, state the departure from imaging guidelines.** The ISIC standards advise oblique light and no direct flash [10, 11]. Those are for clinical documentation. The plan's on-axis cross-polarised ring flash is a deliberate choice for glare control and fixed output, and the plan should say so in one line so a reviewer does not read it as an oversight.
3. **C2, correction model.** Name the model and test two in rung 2: a 3 × 3 linear fit to the card [6] and a per-image second-order polynomial [7]. Paper 7 is the closest published drift figure with the same card, and only for card patches. Add the warning from [6]: the card corrects only light that also falls on the card, so the card must sit in the same plane and the same light as the spot.
4. **C5, software trap.** Compute L\*a\*b\* in our own code from linear values. Photoshop's 8-bit Lab histogram is scaled and offset [5], and a tool that reads it naively gives wrong L\*.
5. **C7, add a framing overlay.** A live overlay of the baseline frame that only releases the shutter when framing matches is cheap and worked for repositioning [4]. It does not replace the spacer, because distance still moved L\* in that study.
6. **Section 4.2, registration model.** Allow rotation and scale, not only shift: the two registration papers use a geometric transform from keypoints [2] and a rigid-plus-scaling step before any deformable step [3]. Keep a manual control-point fallback when automatic matching finds too few points [2], and log how often it is used. Other spots near the target can serve as anchors [3], as long as the target spot itself stays masked out.
7. **Section 4.3, area.** Expect segmentation to fail first on low-contrast lesions and curved skin [1, 12]. The only repeat-photo area error for a white lesion (vitiligo, UV photography) is about ten times the area of a 2 mm spot [12], so A(t) at 2 mm needs its own phantom test and cannot borrow that figure. UV (365 nm) capture as a segmentation aid is a lead only; nobody here tested it on IGH.
8. **Section 2.3, perception threshold.** Two papers cite perception thresholds secondhand: a facial-skin threshold attributed to Lagouvardos et al. in [4], and dentistry tolerances in [8]. Both are leads for the missing `T_match` source, not usable numbers until the primary papers are read.
9. **Section 7.** Mark these 13 as read, with the result that none gives a skin L\* smallest detectable change between visits.

### The two placement simulations (`experiments/drift_sim.py`, `experiments/placement_sim.py`)

1. **Rotation and scale between visits.** `placement_sim.py` registers by masked cross-correlation over shifts only. Real repeat photos also rotate and change scale slightly; the face app accepted framing when the area of its landmark triangle was within a tolerance k of the target, with k = 0.05 at the looser setting [4], which reads as [about ±5% in area, ±2.5% in linear size]. Add cases with [small rotations of a few degrees and scale changes of a few percent] and test a similarity registration against the current shift-only one. The magnitudes are my guess and should be set from rung 2 phantom repeats.
2. **Perspective tilt.** C6 is still marked not covered in the plan's table. Add a tilt that turns the disc into an ellipse, since the guidelines also flag that perpendicularity is hard to assure [10].
3. **Light that the card cannot see.** Add a shadow or gradient over the spot but not over the card [6], and an illuminant change between visits that a per-channel gain or a 3 × 3 matrix does not fully undo [8]. Ring normalisation handles uniform drift today; these cases test whether it still does.
4. **Feature-poor skin.** Skin often has few strong keypoints [2]. Report the registration refusal rate at lower mottle than the current 5%, not only the error when it succeeds.
5. **Neighbouring spots.** Put one or two other synthetic spots outside the ring, to test both the anchor effect [3] and that the exclusion mask keeps them out of R.

Some of these (rotation, uneven light) may already be covered by the harder line-up tests being written in another thread; scale, perspective, an illuminant change and neighbouring spots are the additions to check against that list.

## How to re-check this page

```
python3 tools/photo_methods_check.py                 # every quote against its saved source
python3 tools/photo_methods_check.py <excerpts_dir>  # if the texts live elsewhere
```

The saved texts are in the project files `papers/excerpts/`: `pmc_9907704.txt`, `pmc_9424913.txt`, `pmc_12352120.txt`, `pmc_11230921.txt`, `pmc_3778111.txt`, `pmc_4851905.txt`, `pmc_13636185.txt`, `pmc_9360608.txt`, `pmc_12027704.txt`, `pmc_7496888.txt`, `pmc_13237307.txt`, `katragadda2017.txt`, `finnane2017.txt`. They were made from the publisher XML (title, abstract, body, tables and figure captions) or, for the two PDFs, with `pdftotext`.
