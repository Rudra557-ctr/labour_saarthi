# Data Sources

Generated from `config/sources.yaml` — the registry is the authority, this file is a view of it.
Regenerate with `make docs-sources`.

`verification_status`: **VERIFIED_URL** = URL confirmed reachable · **VERIFIED_EXISTS** = source confirmed,
exact download URL not fixed · **UNVERIFIED** = access not yet established.

| source_id | role | publisher | access | geo available | occupation coding | period grain | status | acquired |
|---|---|---|---|---|---|---|---|---|
| `NCO_2015` | taxonomy | Directorate General of Employment, Ministry of | PDF | not_applicable | NCO_2015 | not_applicable | VERIFIED_URL | 2026-10-02 (3 files) |
| `NCO_2015_NAT_TABLE` | taxonomy | Directorate General of Employment, Ministry of | PORTAL_REPORT | not_applicable | NCO_2015 | not_applicable | VERIFIED_URL | 2026-10-02 (7 files) |
| `NCVET_NCO_MAPPING_REPORT` | taxonomy | National Council for Vocational Education and  | PDF | not_applicable | NCO_2015 | not_applicable | VERIFIED_URL | 2026-10-02 (1 files) |
| `NQR_QUALIFICATIONS` | taxonomy | NCVET | PORTAL_REPORT | not_applicable | unknown | not_applicable | VERIFIED_EXISTS | 2026-10-02 (1 files) |
| `NSQF_NOTIFICATION_2023` | taxonomy | NCVET | PDF | not_applicable | not_applicable | not_applicable | VERIFIED_EXISTS | — |
| `LGD_DIRECTORY` | reference | Ministry of Panchayati Raj | PORTAL_FORM | state, district, sub_district, local_body, village | not_applicable | snapshot | VERIFIED_URL | — |
| `NCS_VACANCIES` | demand | Directorate General of Employment, Ministry of | PORTAL_REPORT | national, state, district | unknown | snapshot | VERIFIED_EXISTS | — |
| `ESHRAM_REGISTRATIONS` | supply | Ministry of Labour & Employment | PORTAL_REPORT | national, state, district | NCO_2015_derived | snapshot (cumulative stock) | VERIFIED_EXISTS | — |
| `PLFS` | context | National Statistics Office, MoSPI | PDF | national (monthly), state (quarterly/annual) | NCO_2015 | month, quarter, year | VERIFIED_URL | 2026-10-02 (2 files) |
| `PMKVY_DISTRICT_OUTCOMES` | training | Ministry of Skill Development and Entrepreneur | BULK_DOWNLOAD | district | none (scheme training-type split only) | snapshot as on 2022-04-21 | VERIFIED_URL | — |
| `DGT_ITI_CAPACITY` | training | Directorate General of Training, MSDE | UNKNOWN | unknown | DGT_TRADE | academic_year | UNVERIFIED | — |
| `DATAMEET_DISTRICT_BOUNDARIES` | reference | DataMeet (community) | BULK_DOWNLOAD | district | not_applicable | snapshot | VERIFIED_EXISTS | — |
| `NQR_SECTORS` | taxonomy | NCVET | PORTAL_REPORT | not_applicable | not_applicable | not_applicable | VERIFIED_URL | 2026-10-02 (1 files) |
| `DATAMEET_DISTRICT_ATTRS` | reference | DataMeet (community) - derived from Census of  | BULK_DOWNLOAD | district | not_applicable | snapshot (Census 2011 vintage) | VERIFIED_URL | 2026-10-02 (1 files) |
| `NCS_API_PUBLIC` | reference | Directorate General of Employment, Ministry of | API | state | ncs_skill_keyword | snapshot | VERIFIED_URL | — |
| `NCS_PARLIAMENTARY_ANSWERS` | demand | Ministry of Labour & Employment | PDF | national, state | ncs_sector (22 categories, NOT NCO, NOT the NQR 59 sectors) | cumulative since inception, as-on a stated date | VERIFIED_URL | 2026-10-02 (4 files) |
| `LGD_DISTRICTS_DATAGOVIN` | reference | Ministry of Panchayati Raj (published via NIC  | BULK_DOWNLOAD | state, district, sub_district | not_applicable | snapshot (2023-11-30 / 2023-12-01 vintages) | VERIFIED_URL | 2026-10-02 (3 files) |
| `UDYAM_DISTRICT_MSME` | context | Ministry of Micro, Small and Medium Enterprise | BULK_DOWNLOAD | district | not_applicable | cumulative snapshot as on 2023-12-21 | VERIFIED_URL | 2026-10-02 (2 files) |
| `CENSUS_2011_B_SERIES` | context | Office of the Registrar General and Census Com | BULK_DOWNLOAD | national, state, district (urban to city level) | NCO_2004 | Census 2011 (single historical point) | VERIFIED_EXISTS | — |
| `STATE_EMPLOYMENT_PORTALS` | demand | State Directorates of Employment / Skill Devel | UNKNOWN | district (claimed by portal UI) | unknown | unknown | UNVERIFIED | — |
| `NIC_2008` | taxonomy | Ministry of Statistics and Programme Implement | PDF | not_applicable | not_applicable | not_applicable | VERIFIED_URL | 2026-10-04 (1 files) |
| `CENSUS_2011_B24` | context | Office of the Registrar General and Census Com | BULK_DOWNLOAD | state, district | NCO_2004 | Census 2011 (single historical point) | VERIFIED_URL | 2026-10-04 (3 files) |
| `ILOSTAT_EMP_ECO_OCU` | context | International Labour Organization (derived fro | API | national | ISCO_08_MAJOR_GROUP | year | VERIFIED_URL | 2026-10-04 (3 files) |
| `MSDE_ANNUAL_REPORT_2023_24` | training | Ministry of Skill Development and Entrepreneur | PDF | national, state | DGT_TRADE_NSQF (no NCO codes published) | scheme period / as-on date | VERIFIED_URL | 2026-10-04 (1 files) |
| `DGT_CTS_CURRICULUM` | taxonomy | Directorate General of Training, Ministry of S | PDF | not_applicable | NCO_2015 | not_applicable | VERIFIED_URL | 2026-10-04 (2 files) |
| `DATA_GOV_IN_PLATFORM` | reference | National Informatics Centre | API | varies_by_resource | varies_by_resource | varies_by_resource | VERIFIED_EXISTS | — |

## Per-source notes

### `NCO_2015` — National Classification of Occupations 2015

- **Landing:** https://dge.gov.in/nco-2015
- **Licence:** Government of India publication; terms not explicitly stated on landing page (verified: false)
- **Authoritative:** true · **Update cadence:** irregular (series revisions: 1946, 1958, 1968, 2004, 2015)
- **Notes:** Aligned to ISCO-2008. Three volumes. Text layer is glyph-encoded subset fonts; extraction requires pdfplumber + manual spot-check validation.

### `NCO_2015_NAT_TABLE` — NCO-2015 occupation table (DGE "NAT" browser)

- **Landing:** https://dge.gov.in/nat
- **Licence:** Government of India portal; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** unknown
- **Notes:** STRUCTURED OFFICIAL SOURCE - discovered 2026-10-02 via the NCVET mapping report (Annexure IX Note 1 names this as MoLE's NCO search engine). Paginated HTML table with columns: S.No., Occupational Title, NCO 2015, NCO 2004, Division, Sub Division, Group, Family. Pages 0-6 inclusive (500 rows per page, 447 on the last) = 3447 occupation rows. This is strongly preferred over PDF extraction for occupation_master, and it additionally carries an OFFICIAL NCO-2004 to NCO-2015 concordance.

### `NCVET_NCO_MAPPING_REPORT` — Report on Mapping of Qualifications with NCO Codes

- **Landing:** https://ncvet.gov.in/whats-new/
- **Licence:** Government of India publication; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** one-off report
- **Notes:** HIGHEST PRIORITY. Committee spanned MoLE, MSDE, UGC, AICTE, NCVET, DGT, NSDC and Awarding Bodies. Sub-groups (DGT, NIELIT, SSCs) were tasked with confirming/correcting NCO codes ALREADY ASSIGNED to NSQF-aligned qualifications. Whether this document contains a full QP->NCO crosswalk table or only guidelines determines whether our qualification->occupation mapping is authority=OFFICIAL or authority=PROJECT.

### `NQR_QUALIFICATIONS` — National Qualifications Register

- **Landing:** https://nqr.gov.in/
- **Licence:** Government of India publication; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** continuous as qualifications are approved
- **Notes:** Official register of NSQF-aligned approved qualifications across 59 sectors. Per-qualification Q-File dossier incl. Model Curriculum and Occupational Maps. NO bulk export or API found. Observed per-file URL pattern: nqr.gov.in/qualification/file/QF_<code>_<name>_V<n>.pdf Whether a Q-File carries an explicit NCO code field: UNVERIFIED.

### `NSQF_NOTIFICATION_2023` — National Skills Qualifications Framework notification (6 June 2023)

- **Landing:** https://ncvet.gov.in/?p=11295
- **Licence:** Government of India gazette notification (verified: false)
- **Authoritative:** true · **Update cadence:** superseded 27 Dec 2013 notification
- **Notes:** Eight levels (1-8) including half levels: 1, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 8. Needed to seed the NSQF level reference.

### `LGD_DIRECTORY` — Local Government Directory

- **Landing:** https://lgdirectory.gov.in/downloadDirectory.do
- **Licence:** Government of India open directory; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** monthly (1st of each month)
- **Notes:** THE geography spine. Form-driven download, NO API. Monthly update cadence is why location_change_event is required rather than optional. data.gov.in mirrors exist but their API is reported absent.

### `NCS_VACANCIES` — National Career Service - vacancies and jobseekers

- **Landing:** https://www.ncs.gov.in/_layouts/15/ncsp/ViewStaticReport.aspx
- **Licence:** Government of India portal; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** unknown
- **Notes:** DECIDES D-04. District-level active vacancies/employers appear on the portal static report page. Whether vacancies are NCO-coded, and whether occupation x district is published JOINTLY, is UNVERIFIED. If NCO-coded at district level, this is the primary official demand source.

### `ESHRAM_REGISTRATIONS` — e-Shram unorganised worker registrations

- **Landing:** https://eshram.gov.in/
- **Licence:** Government of India portal; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** continuous
- **Notes:** Occupation capture is stated to be BASED ON NCO-2015, structured as 30 broad sector categories, 190 broad occupation families, ~400 occupations. This makes map_eshram_occupation_to_nco structural rather than invented. MEASURE IS A CUMULATIVE REGISTRATION STOCK - not employment, not vacancies. Whether occupation x district is published JOINTLY: UNVERIFIED.

### `PLFS` — Periodic Labour Force Survey

- **Landing:** https://mospi.gov.in/
- **Licence:** Government of India publication (verified: false)
- **Authoritative:** true · **Update cadence:** monthly bulletins since April 2025
- **Notes:** DISTRICT-LEVEL ESTIMATES ARE NOT VALID. Survey with sampling error; must carry standard errors and must never be apportioned to districts in a fact table. Post-Jan-2025 design: FSUs 12,800 -> 22,594, ~270,472 households, monthly estimates at ALL-INDIA level only, CWS approach.

### `PMKVY_DISTRICT_OUTCOMES` — District-wise enrolled, trained, assessed, certified and placed under PMKVY

- **Landing:** https://www.data.gov.in/resource/district-wise-enrolled-trained-assessed-certified-placed-under-pmkvy-21-april-2022
- **Licence:** Government Open Data Licence - India (to confirm per resource) (verified: false)
- **Authoritative:** true · **Update cadence:** unknown; this vintage is 2022
- **Notes:** Covers 28 states, 8 UTs, 720 districts. Splits RPL / Short Term Training / Special Projects. API reported ABSENT for this resource. STALE VINTAGE - a newer release must be searched for (Skill India Digital Hub / PMKVY 4.0). NOTE: this is district x scheme-training-type, NOT district x trade.

### `DGT_ITI_CAPACITY` — DGT / ITI Craftsman Training Scheme capacity and admissions

- **Landing:** https://dgt.gov.in/
- **Licence:** unknown (verified: false)
- **Authoritative:** true · **Update cadence:** unknown
- **Notes:** AT RISK. Figures surface via parliamentary answers and CONFLICT between sources (~25.77 lakh seats with 12.25 lakh admitted for 2021-22 in one answer vs ~35 lakh seats cited for 2021 in another). NCVT MIS (ncvtmis.gov.in) appears to be the operational repository. Trade x district open data NOT FOUND. If unavailable, long-term training capacity enters at a coarser grain and must be labelled as such.

### `DATAMEET_DISTRICT_BOUNDARIES` — India district boundaries

- **Landing:** https://projects.datameet.org/maps/districts/
- **Licence:** Creative Commons Attribution 2.5 India (verified: true)
- **Authoritative:** false · **Update cadence:** irregular
- **Notes:** NOT a government source - community-maintained, flagged accordingly. Needed only for map rendering (Step 0 R5), never for analysis. For a government-facing tool the official Survey of India external boundary should be used for the national outline. Disputed-boundary depiction is politically sensitive.

### `NQR_SECTORS` — NQR sector listing

- **Landing:** https://nqr.gov.in/sectors
- **Licence:** Government of India portal; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** unknown
- **Notes:** Plain-HTML sector listing page, used to seed sector_master. NOTE: NCVET documentation states the NQR covers 59 sectors; the number of distinct sector entries recoverable from this page is recorded by the build and any shortfall is reported rather than padded.

### `DATAMEET_DISTRICT_ATTRS` — Census 2011 district attribute table (DataMeet maps)

- **Landing:** https://github.com/datameet/maps/tree/master/Districts/Census_2011
- **Licence:** repository licence MIT; project site states CC-BY 2.5 India - DISCREPANCY, see notes (verified: false)
- **Authoritative:** false · **Update cadence:** irregular
- **Notes:** NOT AUTHORITATIVE for LGD. Acquired as a CANDIDATE district universe only (shapefile .dbf attribute table, read without geospatial dependencies), because LGD bulk download is blocked without browser automation. Census 2011 district codes are NOT LGD codes and the two must not be conflated. Loaded to data/staging, never to location_master. Licence discrepancy between repo (MIT) and project site (CC-BY 2.5 IN) is unresolved and must be settled before any public redistribution of derived geometry.

### `NCS_API_PUBLIC` — National Career Service public web API (api.ncs.gov.in)

- **Landing:** https://api.ncs.gov.in/
- **Licence:** no published terms located; Government of India portal API - LICENCE UNCLEAR (verified: false)
- **Authoritative:** true · **Update cadence:** continuous
- **Notes:** Discovered 2026-10-02. These are the endpoints the PUBLIC, UNAUTHENTICATED ncs.gov.in homepage calls; no authentication was used or bypassed. No public API specification exists (/v3/api-docs 500, /openapi.json 401), so this is an undocumented surface and terms of use are UNCLEAR - must be confirmed with DGE before any production or published use. WORKING: /api/location/state returns 39 state names with standard Indian state codes (Bihar 10, Maharashtra 27, Tamil Nadu 33 - these match the Census/LGD state numbering, which is useful for the geography spine but is NOT a substitute for LGD district codes). WORKING: /employer-service/api/v1/hiring/top-companies?year=&limit= returns employer-level totalVacancies - real demand data, but by COMPANY, with no location, occupation or date dimension. WORKING: /api/jobseeker/profiles/career-timeline/get-skills?keyword= returns an id+keyword job-title/skill dictionary, usable as mapping input, not demand. NOT USABLE: /api/locations returns an ENCRYPTED payload (opaque ciphertext), so the district list cannot be read from it. NO job-search / vacancy-by-location / vacancy-by-occupation endpoint was found on this public surface.

### `NCS_PARLIAMENTARY_ANSWERS` — NCS vacancy statistics in Parliament answers (Lok Sabha / Rajya Sabha)

- **Landing:** https://dge.gov.in/
- **Licence:** Parliament of India / Government of India published answer (verified: false)
- **Authoritative:** true · **Update cadence:** irregular (per question answered)
- **Notes:** THE BEST REAL OFFICIAL DEMAND DATA LOCATED. Verified by extraction of 4 PDFs. Structure per answer: gender-wise table; STATE-WISE vacancies (39 rows, absolute numbers); SECTOR-WISE vacancies (22 rows, in lakh). Reconciliation PASSED: state rows sum exactly to the published grand total 35,275,833 as on 2024-11-15. CRITICAL LIMITATIONS, all verified not assumed: (1) the measure is CUMULATIVE VACANCIES MOBILISED SINCE INCEPTION - a stock, not a monthly flow. A flow can only be derived by differencing two dated snapshots. (2) 20,507,320 of 35,275,833 vacancies (58.1%) are booked to "Multiple States/PAN India" and are therefore NOT attributable to any state. Only 41.9% is state-attributable. (3) state-wise and sector-wise are SEPARATE MARGINAL tables. There is NO joint state x sector cross-tabulation, so state x sector cannot be derived from them. (4) NO district. NO occupation. NO NCO code. NO time series within a document. (5) units differ between tables (absolute for state, lakh for sector). NOTE: URLs use https://dge.gov.in/sites/default/files/<YYYY-MM>/<id>_e.pdf . The /dge/sites/... form reported by web search returns HTTP 404.

### `LGD_DISTRICTS_DATAGOVIN` — Local Government Directory - Districts (data.gov.in mirror)

- **Landing:** https://www.data.gov.in/resource/local-government-directory-lgd-districts
- **Licence:** Government Open Data Licence - India (per resource, to confirm) (verified: false)
- **Authoritative:** true · **Update cadence:** mirror is static; LGD itself updates monthly
- **Notes:** DISCOVERED Step 1.6. This is the route around the LGD CAPTCHA: the data.gov.in resource page embeds a DIRECT, KEYLESS file URL in its Nuxt SSR payload (extracted by scripts/probe_datagovin.py): https://www.data.gov.in/files/ogdpv2dms/s3fs-public/datafile/lgd_districts.csv and an API resource UUID 37231365-78ba-44d5-ac22-3deec40b9197 for use with a registered data.gov.in API key. RESOLVED Step 1.7: the WWW host 403s but the APEX host serves the files. Working base: https://data.gov.in/files/ogdpv2dms/s3fs-public/datafile/ VALIDATED 2026-10-02: lgd_states.csv 36 rows (28 S + 8 U, state_code unique, vintage 2023-12-01); lgd_districts.csv 785 rows (district_code unique, all 36 states present, vintage 2023-11-30); lgd_subdistricts.csv 1.27 MB. lgd_districts.csv CARRIES AN OFFICIAL LGD <-> CENSUS-2011 DISTRICT CROSSWALK (district_census2011_code), which is what makes Census B-series joinable. KEY LIMITATION: 125 of 785 districts (15.9%) have district_census2011_code '000' - they post-date Census 2011, so they cannot be joined to any Census table. Pilot states: Maharashtra 36 districts (1 unjoinable), Tamil Nadu 38 (6 unjoinable, 15.8%), Uttar Pradesh 75 (4 unjoinable). SECOND LIMITATION: this mirror is a 2023-11-30 snapshot, while LGD itself updates monthly - it is roughly two years stale and is NOT a live feed. THIRD LIMITATION: the CSV does NOT expose split/merge/rename events, parents or effective dates. Absence of a Census-2011 code is the only change evidence it provides, so location_change_event cannot be populated from it.

### `UDYAM_DISTRICT_MSME` — District-wise MSME enterprises registered under Udyam

- **Landing:** https://www.data.gov.in/resource/district-wise-total-msme-registered-enterprises-under-udyam-registration-till-last-date
- **Licence:** Government Open Data Licence - India (per resource, to confirm) (verified: false)
- **Authoritative:** true · **Update cadence:** catalogue claims daily; files are a 2023-12-21 snapshot (claim contradicted)
- **Notes:** DISCOVERED Step 1.6. The strongest DISTRICT-LEVEL real signal found. Catalogue description (IndiaAI AIKosh): "Daily updated district-wise dataset of total MSMEs (Micro, Small, Medium) registered under UDYAM Registration across India with LG directory codes." The LGD district codes are what make it joinable to our geography spine. ROLE: this is an ESTABLISHMENT / INDUSTRY-STRUCTURE signal, NOT labour demand. Enterprise registrations are not vacancies and must never be labelled as such. Its legitimate use is as an evidence-based district allocation basis and as a context feature. Keyless file URLs extracted from the resource pages: .../datafile/district_level_total_Registered_msme.csv?VersionId=105172500341441 .../datafile/district_level_service_msme.csv?VersionId=105172390466305 API UUIDs: f8cd85a1-f9b8-4ff1-b195-9f75c10eb338 (total), c3dfe7e6-0cfd-4ddb-8f79-9cb3695d9866 (services). VALIDATED 2026-10-02 via the apex host. Both files: 785 rows, columns state_name, lg_dist_code, district_name, micro, small, medium, total, last_updated. 785/785 lg_dist_code values join to lgd_districts.district_code - a clean 100% join. CONTRADICTION FOUND: the catalogue calls it "daily updated", but the actual files carry last_updated = 2023-12-21 for every row. It is a Dec-2023 SNAPSHOT, not a daily feed. The catalogue claim is wrong. MISSINGNESS IS REAL: 'NA' appears in small (30 districts) and medium (123 districts). These must stay missing - never zero-filled. MEASURE: cumulative registered enterprise COUNTS by size class, not a flow.

### `CENSUS_2011_B_SERIES` — Census 2011 B-series economic tables (occupational classification of workers)

- **Landing:** https://censusindia.gov.in/nada/index.php/catalog
- **Licence:** Government of India / ORGI published tables; terms to confirm (verified: false)
- **Authoritative:** true · **Update cadence:** decennial; next census not yet published
- **Notes:** DISCOVERED Step 1.6. Tables B-24 and B-27 give occupational classification of main workers by NCO DIVISION and GROUP down to DISTRICT level, as XLSX from the ORGI digital library. WHY THIS MATTERS: it is the only verified route to real DISTRICT x OCCUPATION information, and it is coded in NCO-2004 - for which we already hold an OFFICIAL NCO-2004 -> NCO-2015 concordance (standardized/map_nco2004_to_nco2015.parquet, 3447 rows, authority=OFFICIAL). CLASSIFICATION, not negotiable: this is HISTORICAL WORKFORCE STRUCTURE as at 2011. It is NOT current employer demand and must never be relabelled as demand. Legitimate use: district x occupation allocation weights and context features, clearly marked ESTIMATED when used that way.

### `STATE_EMPLOYMENT_PORTALS` — State employment-exchange portals (Maharashtra, Uttar Pradesh, Tamil Nadu)

- **Landing:** https://rojgar.mahaswayam.gov.in/
- **Licence:** unknown (verified: false)
- **Authoritative:** true · **Update cadence:** unknown
- **Notes:** LEAD ONLY, Step 1.6. All three pilot states run employment portals whose UI offers DISTRICT-WISE vacancy search - potentially the district-level demand signal the project needs, for exactly our pilot states. Probe results: rojgar.mahaswayam.gov.in HTTP 200 (21 'vacancy' / 19 'district' mentions, JS-driven, 2 table rows); rojgaarsangam.up.gov.in HTTP 200 with a /JobSearch route; tnvelaivaaippu.gov.in HTTP 200, minimal server-rendered content. NOT PURSUED FURTHER because establishing machine access would require deeper interaction with state portals whose terms of use are unknown. This needs (a) a human look in a browser to confirm what is actually published, and (b) a terms-of-use check, before any automated access.

### `NIC_2008` — National Industrial Classification 2008

- **Landing:** https://dge.gov.in/nco-2015
- **Licence:** Government of India publication; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** irregular (NIC series revisions)
- **Notes:** Acquired Step 1.7, formalised Step 2.0. 193 pages. Needed because the NCS vacancy "sector" vocabulary was verified to BE the NIC-2008 section list (20/20 one-to-one name alignment). NIC is an INDUSTRY classification; it is never treated as an occupation classification.

### `CENSUS_2011_B24` — Census 2011 Table B-24: occupational classification of main workers

- **Landing:** https://censusindia.gov.in/nada/index.php/catalog/13648
- **Licence:** Government of India / ORGI published tables; terms to confirm (verified: false)
- **Authoritative:** true · **Update cadence:** decennial
- **Notes:** ACQUIRED Step 3.0. censusindia.gov.in serves only its leaf certificate and omits the emSign intermediate CA, so strict TLS clients fail with "unable to get local issuer certificate". Resolved by fetching that intermediate from the CA repository URL the server's own certificate advertises in its AIA extension, and appending it to the certifi roots. The completed chain verifies to the publicly trusted emSign Root CA - G1 (openssl: "Verify return code: 0 (ok)"). Certificate verification remains FULLY ENABLED; verify=False is used nowhere. See config/certs/README.md. STRUCTURE (verified by reading the files): columns are Table name, State code, District code, Area Name, Division, Sub-Division, NCO name, Total/Rural/Urban, Persons, Males, Females. District code '000' denotes the state total; other codes are districts. Occupation is NCO-2004 at DIVISION (1-digit) and SUB-DIVISION (2-digit) level only - NOT the 8-digit codes our official concordance keys on. CLASSIFICATION: HISTORICAL WORKFORCE STRUCTURE as at 2011. It is NOT employer demand and must never be relabelled as demand. SCOPE NOTE: B-24 covers main workers in NON-HOUSEHOLD industry, trade, business, profession or service - it is not all workers. Catalogue numbering: catalog/(13648 + census_state_code).

### `ILOSTAT_EMP_ECO_OCU` — ILOSTAT: Employment by economic activity and occupation (India)

- **Landing:** https://rplumber.ilo.org/__docs__/
- **Licence:** ILO terms of use; ILOSTAT data is published for public reuse with attribution - CONFIRM exact terms before publication (verified: false)
- **Authoritative:** true · **Update cadence:** annual (last update 2026-10-02 per ILOSTAT catalogue)
- **Notes:** RESOLVES the industry->occupation bridge question, at NATIONAL level only. Indicator EMP_TEMP_ECO_OCU_NB_A, "Employment by economic activity and occupation (thousands)", annual, ILO Labour Force Statistics database. PROVENANCE: for India the source code is BA:14121 = "LFS - Periodic Labour Force Survey" - i.e. this IS India's own PLFS, harmonised and published by the ILO as a cross-tabulation that MoSPI does not publish directly. STRUCTURE (verified): classif1 = economic activity (ISIC-Rev.4 section), classif2 = occupation (ISCO-08 major group), obs_value in THOUSANDS of persons. For India, 751 rows at ISIC4-section x ISCO08-major-group level across 2022, 2023, 2024, 2025. For 2025: 20 sections (A-T) + TOTAL x 9 major groups, 184 of 189 cells populated. WHY IT BRIDGES: NIC-2008 is the Indian adaptation of ISIC-Rev.4 and its section letters/titles align (verified against the official NIC-2008 PDF); NCO-2015 has a documented ONE-TO-ONE correspondence with ISCO-08 where the first digit is the Division/Major Group (NCVET report, Annexure IX s.3). So ISIC4 section x ISCO08 major group maps to NIC-2008 section x NCO-2015 division without inventing anything. KEY LIMITATION: ref_area is IND only. There is NO state dimension, so P(occupation | industry, STATE) is NOT available - only P(occupation | industry) nationally.

### `MSDE_ANNUAL_REPORT_2023_24` — MSDE Annual Report 2023-24 (training annexures)

- **Landing:** https://www.msde.gov.in/
- **Licence:** Government of India published annual report; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** annual
- **Notes:** ACQUIRED Step 5.0. 276 pages, 31 annexures. THE FIRST REAL SUPPLY-SIDE DATA in this project, after PMKVY district resources proved inaccessible (PMKVY-210422.csv returns 404 even on the apex data.gov.in host) and the NCVT MIS portal timed out. USABLE ANNEXURES (structures verified by reading the document): Annexure-11 p232 "State wise training details of PMKVY 1.0 (2015-16)" state x {Enrolled, Trained, Assessed, Certified, Placed} + a published Grand Total row for reconciliation. Annexure-14 p237 "State wise progress under Short Term Training (STT) component of CSSM - PMKVY 2.0 (as on 31.03.2024)", same five measures + a published Total row. Annexure-21 p249 "State wise details of PMKKs (as on 31.03.2024)": districts, districts having a PMKK, PMKKs allocated, PMKKs established - TRAINING INFRASTRUCTURE, a different concept from training outcomes. Annexure-22 p251 "List of 155 NSQF Compliant Trades" with entry qualification, NSQF level, duration and revision year - an official TRADE REFERENCE list. GRAIN LIMITATION, stated plainly: these annexures are STATE-level. DISTRICT-level training data remains UNAVAILABLE. Annexure-21 reports a district COUNT per state, which is not district-level training data. OCCUPATION LIMITATION: no annexure publishes an NCO code. Trades carry NSQF level only, so trade -> NCO stays UNMAPPED. Annexures 12/13/16/17/18/20 use nested multi-level headers (STT / RPL / Grand Total sub-columns) and are NOT parsed in this step - deliberately deferred rather than parsed unreliably.

### `DGT_CTS_CURRICULUM` — DGT Craftsmen Training Scheme trade curricula (NSQF-compliant)

- **Landing:** https://dgt.gov.in/CTS
- **Licence:** Government of India published curriculum; terms not explicitly stated (verified: false)
- **Authoritative:** true · **Update cadence:** per curriculum revision (CTS 2.0 / 3.0)
- **Notes:** RESOLVES the trade -> NCO linkage in PRINCIPLE (Step 5.2). Each DGT CTS trade curriculum carries a "GENERAL INFORMATION" table with the official fields `Name of the Trade`, `Trade Code` (DGT/nnnn) and `NCO - 2015` (one or more 8-digit codes), plus `Reference NOS` codes. A narrative "Reference NCO-2015" block repeats the codes with their NCO titles. THIS IS A DIRECT TRADE -> NCO LINK published by DGT itself, so the Trade -> QP -> NCO chain hypothesised in Step 5.1 is NOT required: the shorter chain Trade Code -> curriculum "NCO - 2015" field -> NCO-2015 is official and sufficient. VERIFIED BY EXTRACTION for the two curricula acquired: Fitter DGT/1002 -> 7233.0100 (Fitter, General), 7233.0200 (Fitter, Bench) Electrician DGT/1001 -> 7411.0100 (Electrician General), 7412.0200 (Electrical Fitter) All four codes resolve in occupation_master with MATCHING titles. Both are MULTI-NCO cases, and both NCO codes are retained - neither is arbitrarily chosen. ENUMERATION LIMITATION: no official index of CTS curricula was found. dgt.gov.in/CTS lists no curriculum PDFs; bharatskills.gov.in/Home/CTS is client-rendered and exposes none in its HTML; its /robots.txt returns an HTML page rather than a policy. Curriculum URLs therefore cannot be enumerated by any sanctioned route, and URL brute-forcing was not attempted. The remaining 153 trades are MAPPING_UNKNOWN, NOT MAPPING_DOES_NOT_EXIST - the mapping demonstrably exists in DGT documents we cannot list.

### `DATA_GOV_IN_PLATFORM` — Open Government Data Platform India (access mechanism, not a dataset)

- **Landing:** https://data.gov.in/
- **Licence:** Government Open Data Licence - India (verified: false)
- **Authoritative:** true · **Update cadence:** varies_by_resource
- **Notes:** Platform-level datastore API exists and requires a free API key. CRITICAL NUANCE: API availability is PER RESOURCE, and several resources we need report "API does not exist". Ingestion must therefore support both an API path and a manual-snapshot path per source. Exact endpoint pattern REQUIRES VERIFICATION (two conflicting forms observed).

