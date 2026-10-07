# pyspiro

![logo](https://github.com/OnlineArts/PySpiro/blob/main/pyspiro/data/pyspiro_250x.png?raw=true)

**pyspiro** is a Python package implementing lung function reference equations for spirometry, static lung volumes, diffusion capacity, and oscillometry. It provides predicted values, z-scores, % predicted, lower limits of normal (LLN), and upper limits of normal (ULN) for research and clinical data analysis pipelines, alongside severity classifiers and reference-equation-free physiological quotients.

---

> [!WARNING]
> **For research use only.**
> pyspiro is intended exclusively for scientific research and data analysis. It must **not** be used as a clinical decision-support tool, for patient diagnosis, or for any medical or clinical purpose. The results produced by this package have not been validated for clinical use and do not constitute medical advice. Always consult a qualified healthcare professional for clinical interpretation of lung function tests.

---

## Available reference equations

### Spirometry
| Class | Population | Age range | Publication                                                                                                                    |
|---|---|---|--------------------------------------------------------------------------------------------------------------------------------|
| `LOELOE_2025` | Iranian (Shahedieh PERSIAN cohort) | 38–69 y | Loeloe et al. 2025, DOI: [10.3389/fmed.2025.1480931](https://doi.org/10.3389/fmed.2025.1480931)                                |
| `BOWERMAN_2022` | Race-neutral (GLI global) | 3–95 y | Bowerman et al. 2023, DOI: [10.1164/rccm.202205-0963OC](https://doi.org/10.1164/rccm.202205-0963OC)                            |
| `ALQEREM_2021` | Middle Eastern children (Jordan) | 6–17.75 y | Al-Qerem 2021, DOI: [10.1111/ijcp.14598](https://doi.org/10.1111/ijcp.14598)                                                   |
| `AGARWAL_2020` | Western Indian (rural Pune) | 20–80 y | Agarwal et al. 2020, DOI: [10.1183/13993003.02129-2019](https://doi.org/10.1183/13993003.02129-2019)                           |
| `ALQEREM_2019` | Jordanian (Middle Eastern) | 18–83 y (M) / 18–78 y (F) | Al Qerem et al. 2019, DOI: [10.1080/17476348.2019.1601560](https://doi.org/10.1080/17476348.2019.1601560)                      |
| `JO_2018` | Korean (KNHANES IV & V) | 19–90 y | Jo et al. 2018, DOI: [10.3346/jkms.2018.33.e16](https://doi.org/10.3346/jkms.2018.33.e16)                                      |
| `PRATA_2018` | Black Brazilian adults | 26–82 y (M) / 20–83 y (F) | Prata et al. 2018, DOI: [10.1590/S1806-37562018000000082](https://doi.org/10.1590/S1806-37562018000000082)                     |
| `JIAN_2017` | Han Chinese | 4–80 y | Jian et al. 2017, DOI: [10.21037/jtd.2017.10.110](https://doi.org/10.21037/jtd.2017.10.110)                                    |
| `DESAI_2016` | Western Indian (Mumbai) | 18–82 y (M) / 18–72 y (F) | Desai et al. 2016, DOI: [10.1016/j.ijtb.2016.08.005](https://doi.org/10.1016/j.ijtb.2016.08.005)                               |
| `CHHABRA_2014` | Northern Indian (Delhi, Punjab, Haryana, UP) | 18–71 y (M) / 18–65 y (F) | Chhabra et al. 2014, DOI: [10.5005/ijcdas-56-4-221](https://doi.org/10.5005/ijcdas-56-4-221)                                   |
| `KUBOTA_2014` | JRS (Japanese) | 17–95 y | Kubota et al. 2014, DOI: [10.1016/j.resinv.2014.03.003](https://doi.org/10.1016/j.resinv.2014.03.003)                          |
| `GLI_2012` | Multi-ethnic | 3–95 y | Quanjer et al. 2012, DOI: [10.1183/09031936.00080312](https://doi.org/10.1183/09031936.00080312)                               |
| `KUSTER_2008` | Swiss LuftiBus | 18–80 y | Kuster et al. 2008, DOI: [10.1183/09031936.00091407](https://doi.org/10.1183/09031936.00091407)                                |
| `PEREIRA_2007` | White Brazilian adults | 26–86 y (M) / 20–85 y (F) | Pereira et al. 2007, DOI: [10.1590/S1806-37132007000400008](https://doi.org/10.1590/S1806-37132007000400008)                   |
| `CHOI_2005` | Korean (KNHANES 2001–2002) | 18–80 y | Choi et al. 2005, DOI: [10.4046/trd.2005.58.3.230](https://doi.org/10.4046/trd.2005.58.3.230)                                  |
| `HANKINSON_1999` | NHANES III (US); Caucasian, Black, Mexican-American | 8–80 y | Hankinson et al. 1999, DOI: [10.1164/ajrccm.159.1.9712108](https://doi.org/10.1164/ajrccm.159.1.9712108)                       |
| `LOUW_1996` | South African men (Black, White) | 20–70 y | Louw et al. 1996, S Afr Med J 1996; 86: 814-819. |
| `QUANJER_1995` | White European children | 6–18 y | Quanjer et al. 1995, DOI: [10.1002/ppul.1950190209](https://doi.org/10.1002/ppul.1950190209)                                   |
| `MOKOETLE_1994` | Black South African adults | 20–65 y | Mokoetle et al. 1994, DOI: [10.1136/thx.49.4.340](https://doi.org/10.1136/thx.49.4.340) |
| `ECCS_1993` | European Caucasian | 18–70 y | Quanjer et al. 1993, DOI: [10.1183/09041950.005s1693](https://doi.org/10.1183/09041950.005s1693)                               |
| `WANG_1993` | White & Black children (US) | 6–18 y (M) / 7–18 y (F) | Wang et al. 1993, DOI: [10.1002/ppul.1950150204](https://doi.org/10.1002/ppul.1950150204)                                      |
| `ROBERTS_1991` | White urban (UK) | 18–86 y | Roberts et al. 1991, DOI: [10.1136/thx.46.9.643](https://doi.org/10.1136/thx.46.9.643)                                         |
| `ZAPLETAL_1987` | European children | 6–18 y | Zapletal 1987, DOI: [10.1159/isbn.978-3-318-04125-5](https://doi.org/10.1159/isbn.978-3-318-04125-5)                           |
| `KNUDSON_1983` | Caucasian (US) | 6–90 y (M) / 6–88 y (F) | Knudson et al. 1983, PMID: [6859656](https://pubmed.ncbi.nlm.nih.gov/6859656/)                                                 |
| `CRAPO_1981` | Caucasian (US), non-smokers | 15–91 y (M) / 17–84 y (F) | Crapo et al. 1981, PMID: [7271065](https://pubmed.ncbi.nlm.nih.gov/7271065/)                                                   |
| `SLIMAN_1981` | Jordanian (Amman) | 20–60 y | Sliman et al. 1981, DOI: [10.1136/thx.36.7.546](https://doi.org/10.1136/thx.36.7.546)                                          |
| `WARWICK_1980` | Caucasian children (US) | 0–18 y | Warwick 1980, PMID: [7374636](https://pubmed.ncbi.nlm.nih.gov/7374636/)                                                        |
| `HSU_1979` | White, Black, Mexican-American | 7–20 y (M) / 7–18 y (F) | Hsu et al. 1979, DOI: [10.1016/S0022-3476(79)80075-X](https://doi.org/10.1016/S0022-3476(79)80075-X)                           |
| `MORRIS_1971_1973` | Caucasian (US), non-smokers | 20–90 y | Morris et al. 1971/1973, PMID: [5540840](https://pubmed.ncbi.nlm.nih.gov/5540840/), [4741868](https://pubmed.ncbi.nlm.nih.gov/4741868/) |
| `CHERNIACK_1972` | Caucasian (US) | 15–79 y | Cherniack & Raber 1972, DOI: [10.1164/arrd.1972.106.1.38](https://doi.org/10.1164/arrd.1972.106.1.38) |
| `POLGAR_1971` | Children | 4–17 y | Polgar & Promadhat 1971, DOI: [10.7326/0003-4819-75-5-819_2](https://doi.org/10.7326/0003-4819-75-5-819_2)                     |

> **Classic equations (POLGAR_1971 – QUANJER_1995)** are regression-based, from the pre-LMS era. Only `percent()` returns a value; `lln()`, `uln()`, and `zscore()` return `pd.NA` because no lower/upper limits of normal were published. Among the polynomial equations, `HANKINSON_1999`, `KUSTER_2008`, `PEREIRA_2007`, `PRATA_2018`, `CHHABRA_2014`, and `DESAI_2016` do provide LLN.<br>
> **PEREIRA_2007** (White adults) and **PRATA_2018** (Black adults) are a companion Brazilian pair, derived by overlapping author groups under the same protocol. Prata's central finding is that predicted FVC and FEV1 are significantly lower in Black than in White Brazilian adults — on average 0.30 L and 0.28 L lower in men — so the two populations should not share one equation. Use the set that matches the patient.<br>
> **LOUW_1996** and **MOKOETLE_1994** are linear regression equations for South African populations. Only `percent()` returns a value; `lln()`, `uln()`, and `zscore()` return `pd.NA`. `LOUW_1996` is men-only and requires an `ethnicity` argument (0 = Black, 1 = White); a `spirometer` option selects the Autolink (default) or Vitalograph equations. The companion `KOEGELENBERG_2013` helper supplies the SATS correction factors — 0.9 for black or Asian individuals (ethnicity 0), 0.95 for individuals of mixed ethnicity (ethnicity 1) — via `correct(predicted, ethnicity)`; it is a helper, not a reference equation, and so is absent from the tables above.

#### Parameter availability matrix

`✓` = available, `—` = not available

| Equation | FVC | FEV1 | FEV0.5 | FEV0.75 | FEV3 | FEV6 | SVC | VC | FIVC | FEV1/FVC | FEV1/FEV6 | FEV0.75/FVC | FEV3/FVC |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `LOELOE_2025` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `BOWERMAN_2022` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `ALQEREM_2021` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `AGARWAL_2020` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `ALQEREM_2019` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `JO_2018` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `PRATA_2018` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `JIAN_2017` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `DESAI_2016` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `CHHABRA_2014` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `KUBOTA_2014` | ✓ | ✓ | — | — | — | — | — | ✓ | — | ✓ | — | — | — |
| `GLI_2012` | ✓ | ✓ | — | ✓ | — | — | — | — | — | ✓ | — | ✓ | — |
| `KUSTER_2008` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `PEREIRA_2007` | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | ✓ | — | — |
| `CHOI_2005` | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — | — |
| `HANKINSON_1999` | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | ✓ | — | — |
| `LOUW_1996` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `QUANJER_1995` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `MOKOETLE_1994` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `ECCS_1993` | ✓ | ✓ | — | — | — | — | — | — | ✓ | ✓ | — | — | — |
| `WANG_1993` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `ROBERTS_1991` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `ZAPLETAL_1987` | ✓ | ✓ | — | — | — | — | ✓ | — | — | ✓ | — | — | — |
| `KNUDSON_1983` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `CRAPO_1981` | ✓ | ✓ | ✓ | — | ✓ | — | — | — | — | ✓ | — | — | ✓ |
| `SLIMAN_1981` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `WARWICK_1980` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `HSU_1979` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `MORRIS_1971_1973` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `CHERNIACK_1972` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `POLGAR_1971` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |

| Equation | FEF25-75% | FEF25% | FEF50% | FEF75% | PEF | MVV | FET | LLN / z-score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `LOELOE_2025` | ✓ | — | — | — | — | — | — | ✓ |
| `BOWERMAN_2022` | — | — | — | — | — | — | — | ✓ |
| `ALQEREM_2021` | ✓ | — | — | — | — | — | — | ✓ |
| `AGARWAL_2020` | — | — | — | — | — | — | — | ✓ |
| `ALQEREM_2019` | ✓ | ✓ | ✓ | ✓ | — | — | — | ✓ |
| `JO_2018` | — | — | — | — | — | — | — | ✓ |
| `PRATA_2018` | ✓ | — | ✓ | ✓ | ✓ | — | — | ✓ |
| `JIAN_2017` | ✓ | — | — | — | ✓ | — | — | ✓ |
| `DESAI_2016` | ✓ | — | ✓ | ✓ | ✓ | — | — | ✓ |
| `CHHABRA_2014` | ✓ | — | ✓ | ✓ | ✓ | — | — | ✓ |
| `KUBOTA_2014` | — | — | — | — | — | — | — | ✓ |
| `GLI_2012` | ✓ | — | — | ✓ | — | — | — | ✓ |
| `KUSTER_2008` | — | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| `PEREIRA_2007` | ✓ | — | ✓ | ✓ | ✓ | — | — | ✓ |
| `CHOI_2005` | — | — | — | — | — | — | — | — |
| `HANKINSON_1999` | ✓ | — | — | — | ✓ | — | — | ✓ |
| `LOUW_1996` | — | — | — | — | — | — | — | — |
| `QUANJER_1995` | — | — | — | — | — | — | — | — |
| `MOKOETLE_1994` | — | — | — | — | — | — | — | — |
| `ECCS_1993` | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — |
| `WANG_1993` | ✓ | — | — | — | — | — | — | — |
| `ROBERTS_1991` | — | — | ✓ | — | ✓ | — | — | — |
| `ZAPLETAL_1987` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `KNUDSON_1983` | ✓ | — | ✓ | ✓ | — | — | — | — |
| `CRAPO_1981` | ✓ | — | — | — | — | — | — | — |
| `SLIMAN_1981` | ✓ | — | — | — | — | — | — | ✓ |
| `WARWICK_1980` | — | — | ✓ | ✓ | ✓ | — | ✓ | — |
| `HSU_1979` | ✓ | — | — | — | ✓ | — | — | — |
| `MORRIS_1971_1973` | ✓ | — | — | — | — | — | — | — |
| `CHERNIACK_1972` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `POLGAR_1971` | ✓ | — | — | — | ✓ | ✓ | — | — |

> **LOELOE_2025** uses pre-computed KNN-based lookup tables (age 38–69 y, height 142–189 cm; inputs rounded to the nearest 0.1). `FEV1FVC` is expressed as a **percentage (0–100)**. `lln()` returns the 5th centile; `uln()` is approximated as 2×predicted − LLN. `zscore()` uses the normal approximation ((value − predicted) / ((predicted − LLN) / 1.645)). `lms()` returns `(NA, NA, NA)`. Some tall-female (age, height) combinations have no reference data and return `pd.NA`.<br>
> **AGARWAL_2020** uses pre-computed lookup tables (integer age 20–80, integer height 137–185 cm); inputs are rounded to the nearest integer. `lln()` returns the 5th centile; `uln()` is approximated as 2×predicted − p5. `zscore()` uses the normal approximation (accurate for males; approximate for females where non-normal GAMLSS families were fitted). `lms()` returns `(NA, NA, NA)`.<br>
> **JIAN_2017** `FEV1FVC` is expressed as a **percentage (0–100)**, not a unitless ratio. Pass the measured FEV1/FVC in % (e.g. `83.0`) for `percent()`, `zscore()`, `lln()`, and `uln()`; these methods return LLN/ULN in % as well. `MMEF` corresponds to FEF25-75%.<br>
> **DESAI_2016** `FEV1FVC` is expressed as a **percentage (0–100)**. Weight is required for male PEFR and female FEF75; pass `weight=None` for all other parameters. LLN is computed as predicted − 1.645 × SE.<br>
> **CHHABRA_2014** `FEV1FVC` is expressed as a **percentage (0–100)**. Weight is required for male FVC, male FEF75, and male FEV1FVC; pass `weight=None` for all other parameters. LLN is computed as predicted − 1.645 × SEE.<br>
> **ALQEREM_2019** is a GAMLSS reference; parameters use different distribution families (Normal for male FEV1/FEF25 and female FVC; BCCG/LMS otherwise), captured in `alqerem_2019_coefficients.csv`. Age-splines (`alqerem_2019_splines.csv`, sampled every 0.25 y) are applied where fitted. `FEV1FVC` is expressed as a **percentage (0–100)**. `lms()` returns `(nu, mu, sigma)` for BCCG parameters and `(NA, NA, NA)` for the Normal ones. Where the BCCG skewness constant was not tabulated (male FVC, female FEV1), `nu = 1.0` is used, consistent with the other Model 2/6 parameters.<br>
> **SLIMAN_1981** is the historical Jordanian reference (linear regression). `FEF25_75` is the paper's FMF 25-75%. LLN/ULN and z-scores use the published residual SD (predicted ∓ 1.645 × SD); `lms()` returns `(NA, NA, NA)`. Superseded by `ALQEREM_2019` for most uses but retained for comparison.<br>
> **KUSTER_2008** names its flow parameters MEF75 (= FEF25%), MEF50 (= FEF50%), and MEF25 (= FEF75%).<br>
> **PRATA_2018** `FEV1FVC` is expressed as a **percentage (0–100)**. No weight argument: weight played no role in any equation. LLN is the published 5th percentile of the residuals — subtracted for the linear parameters (FVC, FEV1, FEV1/FVC, PEF) and multiplied for the log-transformed flows. `zscore()`, `uln()`, and `lms()` return `pd.NA` (no SEE was published). As published, the three FEF equations depend on **age alone**, and female PEF carries no height term. The `FEV1FVC` LLN uses the offsets printed in Tables 3/4 (8.70 M, 7.8 F); the paper's Results text rounds these to 9 and 8.<br>
> **PEREIRA_2007** `FEV1FVC` and `FEV1FEV6` are expressed as **percentages (0–100)**, as are the four flow/FVC ratios (`FEF50_FVC`, `FEF75_FVC`, `FEF25_75_FVC`, `FEF75_85_FVC`). Also provides `FEF75_85`. Weight influenced predicted volumes in males only, so Table 3's two models are exposed separately: `FVC`/`FEV6`/`FEV1` (height + age) and `FVC_WT`/`FEV6_WT`/`FEV1_WT` (height + age + weight, males only — these return `pd.NA` for females and when `weight=None`). All other parameters ignore weight. LLN is the published 5th percentile of the residuals; `zscore()`, `uln()`, and `lms()` return `pd.NA`. Male FEF50/FEF75/FEF25-75/FEF75-85 carry no height term, as published. Two coefficients required editorial judgement against the printed tables; see the class docstring.<br>
> **ALQEREM_2021** `FEV1FVC` is expressed as a **percentage (0–100)**. The cohort is Jordanian; the paper's title says "a Middle Eastern population". Age is rounded to the nearest 0.25 y for the age-spline lookup, as for the GLI equations. Two coefficients in the published Table 2 are corrected here, both settled against the author's own data set: the male FVC `log(age)` term is `+0.24743`, not `−0.24743` (as printed it predicts an FVC below the FEV1), and the male FEV1/FVC intercept is `4.5068298`, not `4.5057904` (the printed value is inconsistent with the published Table A4 spline by a constant 0.104%).<br>
> **CHOI_2005** `FEV1FVC` is expressed as a **percentage (0–100)**. Weight is required for FVC and FEV6. `lln()`, `uln()`, and `zscore()` return `pd.NA` (no limits of normal were published).<br>
> **HSU_1979** and **WANG_1993** require an `ethnicity` argument.<br>
> **WANG_1993** currently implements the Male White subgroup only; other subgroups can be added to `wang_1993_coefficients.csv`.

### Multiple breath washout (MBW)
| Class | Population | Age range | Parameters | Publication                                                                                         |
|---|---|---|---|-----------------------------------------------------------------------------------------------------|
| `RAMSEY_2024` | GLI international (race-neutral) | 2–80 y | LCI, FRC | Ramsey et al. 2024, DOI: [10.1183/13993003.00524-2024](https://doi.org/10.1183/13993003.00524-2024) |

RAMSEY_2024 uses the GAMLSS BCCG model with age-dependent spline corrections from the GLI 2024 supplementary material. LCI has no sex or height dependence; FRC depends on sex, age, and height.

### Lung diffusion capacity
| Class | Population | Publication                                                                                             |
|---|---|---------------------------------------------------------------------------------------------------------|
| `SCAPIS_2023` | Swedish, age 50–65 y | Malinovschi et al. 2023, DOI: [10.1164/rccm.202212-2341OC](https://doi.org/10.1164/rccm.202212-2341OC)                            |
| `GLI_2017` | Caucasian, age 5–80 y | Stanojevic et al. 2017, DOI: [10.1183/13993003.00010-2017](https://doi.org/10.1183/13993003.00010-2017) |

### Static lung volumes
| Class | Population | Publication                                                                                       |
|---|---|---------------------------------------------------------------------------------------------------|
| `GLI_2021` | European ancestry, age 5–80 y | Hall et al. 2021, DOI: [10.1183/13993003.00289-2020](https://doi.org/10.1183/13993003.00289-2020) |

### Oscillometry (IOS/FOT)
| Class | Population | Age / height range | Parameters | Publication                                                                                           |
|---|---|---|---|-------------------------------------------------------------------------------------------------------|
| `SCHULZ_2013` | KORA (German), adults | 40–65 y | R10/15/25/35, X10/20/25/35 | Schulz et al. 2013, DOI: [10.1371/journal.pone.0063366](https://doi.org/10.1371/journal.pone.0063366) |
| `CALOGERO_2013` | Caucasian children (Perth/Viterbo) | 92–159 cm | Rrs6/8/10, Xrs6/8/10, AX, Fres | Calogero et al. 2013, DOI: [10.1002/ppul.22699](https://doi.org/10.1002/ppul.22699)                   |

`CALOGERO_2013` uses direct height+sex regression with log/sqrt transformations (not LMS). Z-scores are on the transformed scale; positive z always means worse than predicted. `percent()` is defined for Rrs, AX, and Fres; it returns `pd.NA` for Xrs (signed values). `predicted()` returns the median value directly.

---

## Physiological quotients

| Class | Basis | Parameters | Publication |
|---|---|---|---|
| `KNOX_BROWN_2026` | 1st percentile ("minimally survivable") values from 13 771 UK hospital patients | FEV1, FVC, FEV1/FVC, DLCO, KCO, VA, TLC | Knox-Brown et al. 2026, DOI: [10.1183/13993003.02204-2025](https://doi.org/10.1183/13993003.02204-2025) |
| `MILLER_2010` | The original derivation, from 26 967 subjects; plus height-standardised FEV1 | FEV1Q, FEV1·Ht⁻³, FEV1·Ht⁻² | Miller & Pedersen 2010, DOI: [10.1183/09031936.00110809](https://doi.org/10.1183/09031936.00110809) |

A physiological quotient expresses a measurement as a multiple of the 1st percentile value observed in a hospital lung function population:

```
Q = measured value / 1st percentile value
```

Because the 1st percentiles are stable across age — and across sex for FEV1/FVC, DLCO and KCO — a quotient needs no age, height or ethnicity, and is therefore still defined for patients no reference equation can score (e.g. static lung volumes above age 80, the limit of `GLI_2021`). Miller & Pedersen introduced the idea for FEV1; Knox-Brown et al. independently reproduced their thresholds and extended the approach to six further measures, so the two classes agree exactly on FEV1Q.

Consensus 1st percentiles (`KNOX_BROWN_2026`; `MILLER_2010` publishes the FEV1 row only):

| Parameter | Male | Female |
|---|---|---|
| FEV1, L | 0.50 | 0.40 |
| FVC, L | 1.50 | 1.20 |
| FEV1/FVC, ratio | 0.15 | 0.15 |
| DLCO, mmol·min⁻¹·kPa⁻¹ | 1.60 | 1.60 |
| KCO, mmol·min⁻¹·kPa⁻¹·L⁻¹ | 0.40 | 0.40 |
| VA, L | 2.40 | 2.00 |
| TLC, L | 2.60 | 2.30 |

Both classes derive from `Quotient`, **not** `Reference`: there is no predicted median, z-score or limit of normal to take. The shared API is `percentile1()`, `quotient()`, `band()` (the whole-quotient bands 0–6 of the published survival curves) and a vectorised `compute()`. `KNOX_BROWN_2026` adds `expressions()`, which reads one measurement as quotient, % predicted and z-score side by side, and carries the published survival statistics as data via `hazard_ratio()` and `cohort_reference()`. `MILLER_2010` adds `height_standardised()` for the paper's second proposal, FEV1 divided by height in metres cubed or squared.

> ⚠️ **Not a replacement for reference equations.** The authors state that until the 1st percentiles are replicated in more diverse cohorts and against outcomes other than mortality, "physiological quotients cannot replace reference equation-based metrics"; the derivation cohorts were 95–97% White European.<br>
> **FEV1/FVCQ** was **not** associated with mortality after adjustment (HR 0.99–1.01, p>0.4) and the authors judge it of little clinical benefit.<br>
> **`DLCO_trad` and `KCO_trad`** are unit conversions performed by this package — the thresholds were published in SI units only.<br>
> **The height-standardised indices have no normative range.** Miller & Pedersen publish no predicted value, LLN, centile or z-score for `FEV1·Ht⁻³` or `FEV1·Ht⁻²`; in the paper they are read purely through a survival analysis, which this package does not implement. The paper's table 6 survival polynomials are omitted by design — they do not reproduce the paper's own worked examples; see the class docstring.

---

## Severity classifiers

| Class | Basis | Stages / outputs |
|---|---|---|
| `ATS_ERS_2022` | FEV1/FVC, FVC, FEV1, TLC z-scores | Normal / Obstructive / Restrictive / Mixed / Non-specific pattern |
| `LF_SEVERITY_2022` | Any lung function z-score (parameter-agnostic) | Normal / Mild / Moderate / Severe |
| `BDR_2022` | Pre/post FEV1 and/or FVC vs predicted | Positive (FEV1) / Positive (FVC) / Positive (FEV1 and FVC) / Negative |
| `GOLD` | FEV1 % predicted (COPD) | I–IV (mild to very severe) |
| `GOLD_ABE` | Exacerbation history + CAT / mMRC (COPD) | A / B / E |
| `ECOPD_ROME_2021` | Dyspnea VAS, respiratory rate, heart rate, SaO2 (or change from baseline), CRP, PaCO2, pH (COPD exacerbation) | Mild / Moderate / Severe |
| `STAR` | FEV1/FVC ratio (COPD) | I–IV (mild to very severe) |
| `BODE` | BMI + FEV1 % predicted + mMRC + 6MWT (COPD) | Score 0–10, Quartiles 1–4 |
| `GAP` | Sex + Age + FVC % predicted + DLCO % predicted (IPF) | Score 0–8, Stages I–III |
| `WODEHOUSE_2003` | nNO in ppb (PCD screening) | PCD range / Normal |
| `PCD_SEVERITY` ⚠️ | LCI z-score + FEV1 z-score + nNO (PCD monitoring) | Mild / Moderate / Severe / Inconclusive |

10 published classifiers; `PCD_SEVERITY` is experimental (`UserWarning` on instantiation).

> ⚠️ **`PCD_SEVERITY` is experimental.** No PCD-specific severity staging system is currently endorsed by the ERS, ATS, or any other professional society. The combination logic and the specific thresholds used here (LCI z > 3.0 for severe; FEV1 z < −2.5 for severe) are custom-designed and have not been externally validated or peer-reviewed as a staging instrument. The cited references (Ramsey 2024, Wodehouse 2003) support the individual input parameters but do not define this combined staging scheme. Use for exploratory research only.

---

## Outputs

All equation classes expose a consistent scalar API and a vectorised `compute()` for DataFrames:

| Method | Returns |
|---|---|
| `percent(...)` | Measured value as % of predicted median |
| `zscore(...)` | Z-score relative to the reference distribution |
| `lln(...)` | Lower limit of normal (5th percentile) |
| `uln(...)` | Upper limit of normal (95th percentile) |
| `lms(...)` | Raw (L, M, S) triplet (LMS equations only) |
| `all(...)` | Tuple of (% predicted, z-score, LLN, ULN) |
| `compute(df, parameter, ...)` | Evaluates whole DataFrame columns at once; returns a DataFrame of metrics |

**Conventions**: sex as integer (0 = female, 1 = male); age in years; height in cm; measured values in their natural units (L, L/s, mmol/min/kPa, etc.). FEV1/FVC ratios are passed as a fraction (0–1) for LMS-based equations.

### `compute()` column-mapping arguments

| Argument | Default | Notes |
|---|---|---|
| `sex_col` | `'sex'` | Integer column: 0 = female, 1 = male |
| `age_col` | `'age'` | Numeric, years |
| `height_col` | `'height'` | Numeric, cm |
| `value_col` | `None` | Required for `percent` / `zscore` |
| `ethnicity_col` | `None` | Required for ethnicity-stratified equations (GLI_2012, HANKINSON_1999) |
| `weight_col` | `None` | Required for SCHULZ_2013 `lln` / `uln` |
| `metrics` | `('percent','zscore','lln','uln')` | Any subset |

`compute()` is vectorised: the equation is evaluated on whole columns instead of row by row (100,000 rows take about 0.02–0.2 s, depending on the equation). The result is the same as calling the scalar methods on each row: same values, NA rows, column dtypes and exceptions. Out-of-range messages (`set_silence(False)`) are printed once per row. A subclass that overrides `lms()` or a metric method keeps working: `compute()` then calls the scalar methods per row.

---

## Installation

```bash
pip install pyspiro
```

For centile chart visualisation, install the optional dependencies:

```bash
pip install pyspiro[viz]   # adds matplotlib and scipy
```

---

## Usage examples

### LMS-based equations (GLI_2012, BOWERMAN_2022, GLI_2017, GLI_2021, SCAPIS_2023, KUBOTA_2014)

```python
from pyspiro import GLI_2012, BOWERMAN_2022

# Multi-ethnic equation — ethnicity_col required
gli = GLI_2012()
results = gli.compute(
    df,
    GLI_2012.Parameters.FEV1,
    value_col='fev1',
    ethnicity_col='eth',     # 1=Caucasian, 2=African-American, 3=NE Asian, 4=SE Asian, 5=Other/mixed
)
# DataFrame with columns: percent, zscore, lln, uln — same index as df
df[['fev1_pct', 'fev1_z', 'fev1_lln', 'fev1_uln']] = results

# Race-neutral — no ethnicity_col needed
bow = BOWERMAN_2022()
df[['fvc_pct', 'fvc_z', 'fvc_lln', 'fvc_uln']] = bow.compute(
    df, BOWERMAN_2022.Parameters.FVC, value_col='fvc')
```

Column name defaults are `sex`, `age`, `height`; override any that differ in your DataFrame:

```python
results = gli.compute(
    df, GLI_2012.Parameters.FEV1,
    sex_col='gender', age_col='age_years', height_col='ht_cm',
    value_col='fev1', ethnicity_col='eth',
    metrics=('percent', 'lln'),
)
```

### Polynomial equations (KUSTER_2008, HANKINSON_1999)

```python
from pyspiro import KUSTER_2008, HANKINSON_1999

# KUSTER_2008: no ethnicity stratification
kus = KUSTER_2008()
df['fev1_pct'] = kus.compute(
    df, KUSTER_2008.Parameters.FEV1,
    value_col='fev1', metrics=('percent',))['percent']
df['fev1_lln'] = kus.compute(
    df, KUSTER_2008.Parameters.FEV1_LLN,
    value_col='fev1', metrics=('lln',))['lln']

# HANKINSON_1999: ethnicity_col required (1=Caucasian, 2=African-American, 3=Mexican-American)
han = HANKINSON_1999()
df[['fvc_pct', 'fvc_z', 'fvc_lln', 'fvc_uln']] = han.compute(
    df, HANKINSON_1999.Parameters.FVC,
    value_col='fvc', ethnicity_col='eth')
```

### Oscillometry (SCHULZ_2013)

SCHULZ_2013 uses direct percentile regression. `compute()` produces LLN (5th) and ULN (95th);
the median (50th) is available via `percentiles()`.

```python
from pyspiro import SCHULZ_2013
import pandas as pd

s = SCHULZ_2013()

# p05 and p95 via compute()
result = s.compute(
    df, SCHULZ_2013.Parameters.R10,
    weight_col='weight', metrics=('lln', 'uln'))
df['R10_p05'] = result['lln']
df['R10_p95'] = result['uln']

# p50 via apply (no single-metric method for the median)
df['R10_p50'] = df.apply(
    lambda r: s.percentiles(r.sex, r.age, r.height, r.weight,
                            SCHULZ_2013.Parameters.R10)[1], axis=1)
```

### Scalar methods (single patient)

All equations still support per-call scalar methods for single-patient use:

```python
gli = GLI_2012()
pct = gli.percent(1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.2)
z   = gli.zscore (1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.2)
lln = gli.lln    (1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.2)

bow = BOWERMAN_2022()
pct = bow.percent(1, 40, 175, BOWERMAN_2022.Parameters.FEV1, 3.2)  # no ethnicity

kus = KUSTER_2008()
pct = kus.percent(1, 40, 175, 1, KUSTER_2008.Parameters.FEV1, 3.2)
```

### NHANES III (polynomial equations)

```python
import pandas as pd
from pyspiro import HANKINSON_1999

h = HANKINSON_1999()

# Ethnicity: 1 = Caucasian, 2 = African-American, 3 = Mexican-American
df[['fvc_pct', 'fvc_z', 'fvc_lln', 'fvc_uln']] = df.apply(
    lambda x: pd.Series(
        h.all(x.sex, x.age, x.height, 1, h.Parameters.FVC, x.fvc)
    ),
    axis=1
)
```

### Pediatric oscillometry (CALOGERO_2013)

```python
from pyspiro import CALOGERO_2013

c = CALOGERO_2013()

# Single patient (female, age 7, height 120 cm)
pred   = c.predicted(sex=0, age=7.0, height=120.0, parameter=CALOGERO_2013.Parameters.Rrs6)
z      = c.zscore   (sex=0, age=7.0, height=120.0, parameter=CALOGERO_2013.Parameters.Rrs6, value=8.5)
uln    = c.uln      (sex=0, age=7.0, height=120.0, parameter=CALOGERO_2013.Parameters.Rrs6)
lln_x  = c.lln      (sex=0, age=7.0, height=120.0, parameter=CALOGERO_2013.Parameters.Xrs6)  # most negative normal

# Fres (no sex term — same result for male/female):
fres_uln = c.uln(sex=0, age=7.0, height=120.0, parameter=CALOGERO_2013.Parameters.Fres)

# Batch via compute()
df[['rrs6_z', 'rrs6_lln', 'rrs6_uln']] = c.compute(
    df, CALOGERO_2013.Parameters.Rrs6,
    value_col='rrs6', metrics=('zscore', 'lln', 'uln'))

# Note: height is the predictor; age is accepted but ignored in the regression
```

### Multiple breath washout — LCI and FRC (RAMSEY_2024)

```python
from pyspiro import RAMSEY_2024

r = RAMSEY_2024()

# LCI: no sex or height dependence (pass dummy height or actual height — ignored)
lci_z   = r.zscore(sex=0, age=12.0, height=145.0, parameter=RAMSEY_2024.Parameters.LCI, value=8.5)
lci_uln = r.uln   (sex=0, age=12.0, height=145.0, parameter=RAMSEY_2024.Parameters.LCI)
lci_pct = r.percent(sex=0, age=12.0, height=145.0, parameter=RAMSEY_2024.Parameters.LCI, value=8.5)

# FRC: sex and height matter
frc_z   = r.zscore(sex=1, age=35.0, height=178.0, parameter=RAMSEY_2024.Parameters.FRC, value=3.8)
frc_lln = r.lln   (sex=1, age=35.0, height=178.0, parameter=RAMSEY_2024.Parameters.FRC)

# Batch via compute()
df[['lci_z', 'lci_lln', 'lci_uln']] = r.compute(
    df, RAMSEY_2024.Parameters.LCI,
    value_col='lci', metrics=('zscore', 'lln', 'uln'))
```

### PCD screening and severity (WODEHOUSE_2003, PCD_SEVERITY)

```python
from pyspiro import RAMSEY_2024, GLI_2012, WODEHOUSE_2003, PCD_SEVERITY

# nNO classification (Wodehouse 2003)
w = WODEHOUSE_2003()
print(w.classify(nno_ppb=65))    # 'PCD range'
print(w.classify(nno_ppb=750))   # 'Normal'
print(w.zscore(65))               # z-score relative to healthy controls (~−4.8)

# PCD severity staging
r   = RAMSEY_2024()
gli = GLI_2012()
sev = PCD_SEVERITY()

lci_zscore  = r.zscore(sex=0, age=12.0, height=145.0,
                        parameter=RAMSEY_2024.Parameters.LCI, value=9.2)
fev1_zscore = gli.zscore(0, 12.0, 145.0, 1, GLI_2012.Parameters.FEV1, 1.4)

stage = sev.classify(
    lci_zscore  = lci_zscore,   # from RAMSEY_2024
    nno_ppb     = 65,           # measured nNO; ≥200 ppb → 'Inconclusive'
    fev1_zscore = fev1_zscore,  # from any spirometry reference
)
# → 'Mild', 'Moderate', 'Severe', or 'Inconclusive'
```

### Physiological quotients (KNOX_BROWN_2026, MILLER_2010)

```python
from pyspiro import KNOX_BROWN_2026, MILLER_2010, GLI_2017, GLI_2021

kbq = KNOX_BROWN_2026()
P   = KNOX_BROWN_2026.Parameters

# Q = measured / 1st percentile. Sex is required for FEV1, FVC, VA and TLC...
kbq.quotient(P.FEV1, 1.20, sex=0)   # → 3.0  (1.20 / 0.40)
kbq.quotient(P.FEV1, 1.20, sex=1)   # → 2.4  (1.20 / 0.50)

# ...and ignored for FEV1/FVC, DLCO and KCO, whose 1st percentiles are sex-neutral
kbq.quotient(P.DLCO_SI, 3.20)       # → 2.0  (3.20 / 1.60)
kbq.quotient(P.FEV1FVC, 0.60)       # → 4.0  (ratio as a fraction, not 0–100)

# Whole-quotient band used in the published Kaplan–Meier curves (0–6)
kbq.band(P.FEV1, 1.20, sex=0)       # → 3

# Batch over a cohort
df['FEV1Q'] = kbq.compute(df, P.FEV1, value_col='FEV1')['quotient']
df['DLCOQ'] = kbq.compute(df, P.DLCO_SI, value_col='DLCO', sex_col=None)['quotient']
```

`MILLER_2010` follows the same API, and adds the height-standardised indices (height in cm as everywhere else, converted to metres internally):

```python
miller = MILLER_2010()
M      = MILLER_2010.Parameters

miller.quotient(M.FEV1Q, 1.20, sex=1)              # → 2.40  (same as kbq FEV1Q)
miller.height_standardised(0.67, 176.0)            # → 0.1229  (FEV1·Ht⁻³)
miller.height_standardised(0.67, 176.0, power=2)   # → 0.2163  (FEV1·Ht⁻²)

df['FEV1_HT3'] = miller.compute(df, M.FEV1_HT3)['FEV1_HT3']
```

`expressions()` reads one measurement three ways. Where the equation runs out of range the quotient is still defined:

```python
kbq.expressions(P.TLC, 5.10, sex=1,
                equation=GLI_2021(), equation_parameter=GLI_2021.Parameters.TLC,
                age=82, height=178)
# {'parameter': 'TLC', 'value': 5.1, 'percentile_1': 2.6, 'quotient': 1.96,
#  'band': 1, 'equation': 'GLI_2021', 'percent': <NA>, 'zscore': <NA>}
```

Published survival statistics are carried as data — hazard ratios per 1-unit increase in the quotient, and the quotient distributions of the two derivation cohorts:

```python
kbq.hazard_ratio(P.VA, site='RPH', model='model2')
# {'hr': 0.31, 'ci': (0.28, 0.34), 'p': '<0.001'}

kbq.hazard_ratio(P.DLCO_SI, site='RPH', model='unadjusted')
# {'hr': 0.51, 'ci': (0.49, 0.53), 'p': '<0.001',
#  'c_index': 0.73, 'c_index_ci': (0.72, 0.73)}

kbq.cohort_reference(P.FEV1, site='CUH', stratum='age_ge_70')
# {'n': 1911, 'mean': 4.27, 'sd': 1.51}
```

Sites are `'CUH'` (n=7717, 19% mortality over 5.8 years) and `'RPH'` (n=6054, 39% over 5.5 years); models are `'unadjusted'`, `'model1'` (age, sex, height, smoking, referral reason) and `'model2'` (model 1 plus ethnicity). Strata are `'overall'`, `'male'`, `'female'` and the five age groups.

### COPD severity staging

```python
import pandas as pd
from pyspiro import GLI_2012, GOLD

gli  = GLI_2012()
gold = GOLD()

df['fev1_pct'] = df.apply(
    lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters.FEV1, x.fev1),
    axis=1
)
df['GOLD'] = df.apply(lambda x: gold.classify(FEV1p=x.fev1_pct), axis=1)
df['GOLD'] = pd.Categorical(df['GOLD'], categories=gold.get_order(), ordered=True)
```

---

## Cross-equation comparison

`compare_equations()` returns a DataFrame comparing % predicted and z-score for a single patient across all specified equations. This is useful for sensitivity analyses and understanding how equation choice affects clinical interpretation.

```python
import pandas as pd
from pyspiro import GLI_2012, BOWERMAN_2022, HANKINSON_1999, compare_equations

patient = pd.Series({
    'sex':       1,     # male
    'age':       45.0,
    'height':    175.0,
    'ethnicity': 1,     # Caucasian
    'FEV1':      2.8,
})

result = compare_equations(
    patient,
    GLI_2012.Parameters.FEV1,
    equations=[GLI_2012(), BOWERMAN_2022(), HANKINSON_1999()],
)
print(result)
```

```
         equation  percent_predicted    zscore  applicable
0        GLI_2012              71.12 -2.223992        True
1   BOWERMAN_2022              75.41 -1.685500        True
2  HANKINSON_1999              71.13 -2.450593        True
```

Parameters are matched across equations **by name** (e.g. `FEV1`), so the same
physiological parameter is compared even though each equation encodes it with a
different internal enum value. An equation is marked `applicable=False` only when
it does not define the requested parameter or the inputs fall outside its valid
range.

Pass `equations=None` to compare against all available equations automatically.

### Batch processing a cohort

```python
results = []
for _, row in df.iterrows():
    cmp = compare_equations(row, GLI_2012.Parameters.FEV1,
                            equations=[GLI_2012(), BOWERMAN_2022()])
    cmp['patient_id'] = row['patient_id']
    results.append(cmp)

summary = pd.concat(results, ignore_index=True)
```

---

## Centile chart generation

`plot_centile_curves()` draws lung function percentile curves across the age range supported by an equation. The function returns a `matplotlib.figure.Figure` and can be saved for publication.

Requires `pip install pyspiro[viz]`.

```python
import matplotlib.pyplot as plt
from pyspiro import GLI_2012, plot_centile_curves

gli = GLI_2012()

fig = plot_centile_curves(
    gli,
    sex=1,            # male
    height=175,       # cm
    ethnicity=1,      # Caucasian
    parameter=gli.Parameters.FEV1,
    title="FEV1 reference values — male, 175 cm, Caucasian (GLI 2012)",
)
fig.savefig("fev1_percentiles.png", dpi=300, bbox_inches="tight")
plt.show()
```

Customise the plotted percentiles, age window, and figure size:

```python
fig = plot_centile_curves(
    gli,
    sex=0,
    height=165,
    ethnicity=1,
    parameter=gli.Parameters.FVC,
    age_range=(18, 80),
    percentiles=[5, 50, 95],
    figsize=(10, 6),
)
```

Race-neutral equations (e.g. `BOWERMAN_2022`) do not require an ethnicity argument:

```python
from pyspiro import BOWERMAN_2022, plot_centile_curves

fig = plot_centile_curves(
    BOWERMAN_2022(),
    sex=1,
    height=175,
    parameter=BOWERMAN_2022.Parameters.FEV1,
)
```

### Centiles on a quotient axis

`plot_quotient_centiles()` draws the same centile curves rescaled onto a physiological quotient axis, with the fixed quotient bands overlaid. The equation supplies the centiles; the quotient supplies only the constant denominator and the band grid.

```python
from pyspiro import BOWERMAN_2022, KNOX_BROWN_2026, plot_quotient_centiles

fig = plot_quotient_centiles(
    BOWERMAN_2022(),          # GLI global — supplies the centiles
    KNOX_BROWN_2026(),        # supplies the 0.50 L denominator and Q=1…6 grid
    sex=1,
    height=175,
    parameter=BOWERMAN_2022.Parameters.FEV1,
)
```

Any `Quotient` implementation can be passed as the second argument. Its `Parameters` member is resolved from the equation's by name, with a `Q` suffix accepted — an equation's `FEV1` finds `MILLER_2010.Parameters.FEV1Q`. Pass `quotient_parameter=` where the names differ further; `GLI_2017` calls the SI transfer factor `TLCO`, the quotient calls it `DLCO_SI`:

```python
fig = plot_quotient_centiles(
    GLI_2017(), KNOX_BROWN_2026(),
    sex=1, height=175,
    parameter=GLI_2017.Parameters.TLCO,
    quotient_parameter=KNOX_BROWN_2026.Parameters.DLCO_SI,
)
```

`bands=` overrides the horizontal grid (pass an empty sequence to omit it); `percentiles=`, `age_range=`, `figsize=` and `ax=` behave as in `plot_centile_curves()`.

> **Read the falling curves carefully.** This is *not* a centile chart of the quotient — a quotient has no distribution, only a fixed denominator. The curves fall across age even though the denominator does not, because the underlying reference values fall. With GLI global (`BOWERMAN_2022`) for a 175 cm man, the lower limit of normal is FEV1Q ≈ 6.6 at age 20 and ≈ 3.5 at age 90: a fixed quotient is not a fixed centile. The 1st percentile is age-stable; the quotient it produces is not age-neutral to interpret.

---

## Citation

If you use pyspiro in your research, please cite:

> Hendrik Pott, Roman Martin. pyspiro v0.9.4. doi:10.5281/zenodo.15519193
