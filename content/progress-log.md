## Progress Log

### 27 November 2026 · Batch 3

Contributors: Ben (go-ahead), Claude (extraction, verification, checks).

- Twelve more records passed independent verification and were merged. The ledger now holds 54 rows from 21 studies, and every extracted study carries verbatim quotes.
- The longest quoted gap between a final treatment and an assessment on an IGH row is now 2 months (shin2013 and goldust2013, each a single fractional CO2 laser session). Still no row measures a lasting colour match.
- One letter was excluded because it reports no IGH patients. Four sources are blocked behind paywalls and wait for PDFs.

### 27 November 2026 · Correction

Contributors: Ben (review), Claude (checks).

- Corrected the home page. It said the longest gap between a final treatment and an assessment was four months, after a single freeze. After re-extraction with verbatim quotes, that trial's abstract counts time from the start of treatment, so its gap is not derivable. The ledger check now reports 1 month (deepadarshan2023) as the longest quoted gap on an IGH row, and 0 rows that measure a lasting colour match.
- Merged evidence rows now show the verifier's result and date instead of "PENDING".

### 27 November 2026 · Session 1

Contributors: Ben (brief, question, review), Claude (checks, extraction, code, site).

**Done**

- Re-read every numerical claim in the seed brief's evidence ledger against PubMed abstracts or open full texts. Ten points were corrected, qualified or confirmed; they are listed under Evidence.
- Identified the anchor review: Aravindakshan and colleagues, *Clinical and Experimental Dermatology* 2025, 50(9):1741-1747. It searched to November 2023, included 20 studies and states that follow-up data on how long repigmentation lasts are scarce.
- Ran three dated PubMed queries and one ClinicalTrials.gov query. PubMed returned 20 records since December 2023 and none is a new IGH treatment trial. The registry lists two IGH trials in total.
- Built the evidence table: 20 rows from 13 studies, each with timing after the last treatment, excess pigment, scarring and a verification status.
- Checked the "before and after" image claim. The 13 pairs in the Anhui dataset are vitiligo. No IGH before-and-after image set was found.
- Reproduced the seed brief's alignment formula, confirmed it with an independent pixel model, and extended it to fading, shrinking, dark overshoot and darkening of nearby skin.
- Ran two calculations on published counts: a clustering sensitivity analysis and a denominator audit.
- Built this site from Markdown and CSV files with one build script.
- Added a validator that rejects any evidence record whose numbers lack a verbatim quote, and wrote role definitions for searching, extracting and verifying in later sessions.

**Not done**

- Full texts behind paywalls were not read. Rows that rest on an abstract say so.
- Web of Science, Scopus and data repositories (GEO, BioImage Archive, Zenodo, Figshare) were not searched.
- The registry-posted results of the excimer pilot were not extracted.
- No row has a stored verbatim quote yet; re-extraction with quotes is the first task of the next session.
- Open-access PDFs were read by an automated extractor. Their numbers need a human spot-check against the tables.
- Nothing has been sent to any researcher. The site is not deployed.

**Next**

- Print the dot target and run the repeatability task.
- Read the free full text of the tip cryotherapy trial to resolve its denominators and patient count.
- Decide where corrections should be sent, then publish.
