# pyspiro

![logo](https://github.com/OnlineArts/PySpiro/blob/main/pyspiro/data/pyspiro_250x.png?raw=true)

**pyspiro** is a Python package implementing lung function reference equations for spirometry, static lung volumes, diffusion capacity, and oscillometry. It provides predicted values, z-scores, % predicted, lower limits of normal (LLN), and upper limits of normal (ULN) for research and clinical data analysis pipelines.

---

## Available reference equations

### Spirometry
| Class | Population | Age range | Publication |
|---|---|---|---|
| `BOWERMANN_2022` | Race-neutral (GLI global) | 3–95 y | Bowermann et al. 2023, PMID: 36383197 |
| `KUBOTA_2014` | JRS (Japanese) | 17–95 y | Kubota et al. 2014, PMID: 25278192 |
| `GLI_2012` | Multi-ethnic | 3–95 y | Quanjer et al. 2012, PMID: 22743675 |
| `JO_2018` | Korean (KNHANES IV & V) | 19–90 y | Jo et al. 2018, PMID: 29215803 |
| `KUSTER_2008` | Swiss LuftiBus | 18–80 y | Kuster et al. 2008, PMID: 18057057 |
| `HANKINSON_1999` | NHANES III (US); Caucasian, Black, Mexican-American | 8–80 y | Hankinson et al. 1999, PMID: 9872837 |
| `QUANJER_1995` | White European children | 6–18 y | Quanjer et al. Pediatric Pulmonology 1995; 19: 135–142 |
| `WANG_1993` | White & Black children (US) | 6–18 y (M) / 7–18 y (F) | Wang et al. Pediatric Pulmonology 1993; 15: 75–88 |
| `ECCS_1993` | European Caucasian | 18–70 y | Quanjer et al. ERJ 1992–1993; Suppl. 15–16: 5–40 |
| `ROBERTS_1991` | White urban (UK) | 18–86 y | Roberts et al. Thorax 1991; 46: 643–650 |
| `ZAPLETAL_1987` | European children | 6–18 y | Zapletal. Progress in Respiration Research Vol 22, 1987 |
| `KNUDSON_1983` | Caucasian (US) | 6–90 y (M) / 6–88 y (F) | Knudson et al. ARRD 1983; 127(5–6): 725–734 |
| `CRAPO_1981` | Caucasian (US), non-smokers | 15–91 y (M) / 17–84 y (F) | Crapo et al. ARRD 1981; 123: 659–664 |
| `WARWICK_1980` | Caucasian children (US) | 0–18 y | Warwick. Minnesota Medicine 1977 & 1980 |
| `HSU_1979` | White, Black, Mexican-American | 7–20 y (M) / 7–18 y (F) | Hsu et al. J Pediatr 1979; 95: 14–23 |
| `MORRIS_1973` | Caucasian (US), non-smokers | 20–90 y | Morris et al. ARRD 1971 & 1973 |
| `CHERNIACK_1972` | Caucasian (US) | 15–79 y | Cherniack & Raber. ARRD 1972; 106(1): 38–46 |
| `POLGAR_1971` | Children | 4–17 y | Polgar & Promadhat. Pulmonary Function Testing in Children, 1971 |

> **Note on classic equations (POLGAR_1971 – QUANJER_1995):** These are regression-based equations from the pre-LMS era. Only `percent()` returns a value; `lln()`, `uln()`, and `zscore()` return `pd.NA` because no lower/upper limits of normal were published. `HANKINSON_1999` and `KUSTER_2008` remain the only polynomial equations that provide LLN.

#### Parameter availability matrix

`✓` = available, `—` = not available

| Equation | FVC | FEV1 | FEV0.5 | FEV0.75 | FEV3 | FEV6 | SVC | VC | FIVC | FEV1/FVC | FEV1/FEV6 | FEV0.75/FVC | FEV3/FVC |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `BOWERMANN_2022` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `KUBOTA_2014` | ✓ | ✓ | — | — | — | — | — | ✓ | — | ✓ | — | — | — |
| `GLI_2012` | ✓ | ✓ | — | ✓ | — | — | — | — | — | ✓ | — | ✓ | — |
| `JO_2018` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `KUSTER_2008` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `HANKINSON_1999` | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | ✓ | — | — |
| `QUANJER_1995` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `WANG_1993` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `ECCS_1993` | ✓ | ✓ | — | — | — | — | — | — | ✓ | ✓ | — | — | — |
| `ROBERTS_1991` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `ZAPLETAL_1987` | ✓ | ✓ | — | — | — | — | ✓ | — | — | ✓ | — | — | — |
| `KNUDSON_1983` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `CRAPO_1981` | ✓ | ✓ | ✓ | — | ✓ | — | — | — | — | ✓ | — | — | ✓ |
| `WARWICK_1980` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `HSU_1979` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `MORRIS_1973` | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| `CHERNIACK_1972` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| `POLGAR_1971` | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |

| Equation | FEF25-75% | FEF25% | FEF50% | FEF75% | PEF | MVV | FET | LLN / z-score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `BOWERMANN_2022` | — | — | — | — | — | — | — | ✓ |
| `KUBOTA_2014` | — | — | — | — | — | — | — | ✓ |
| `GLI_2012` | ✓ | — | — | ✓ | — | — | — | ✓ |
| `JO_2018` | — | — | — | — | — | — | — | ✓ |
| `KUSTER_2008` | — | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| `HANKINSON_1999` | ✓ | — | — | — | ✓ | — | — | ✓ |
| `QUANJER_1995` | — | — | — | — | — | — | — | — |
| `WANG_1993` | ✓ | — | — | — | — | — | — | — |
| `ECCS_1993` | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — |
| `ROBERTS_1991` | — | — | ✓ | — | ✓ | — | — | — |
| `ZAPLETAL_1987` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `KNUDSON_1983` | ✓ | — | ✓ | ✓ | — | — | — | — |
| `CRAPO_1981` | ✓ | — | — | — | — | — | — | — |
| `WARWICK_1980` | — | — | ✓ | ✓ | ✓ | — | ✓ | — |
| `HSU_1979` | ✓ | — | — | — | ✓ | — | — | — |
| `MORRIS_1973` | ✓ | — | — | — | — | — | — | — |
| `CHERNIACK_1972` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `POLGAR_1971` | ✓ | — | — | — | ✓ | ✓ | — | — |

> **KUSTER_2008** names its flow parameters MEF75 (= FEF25%), MEF50 (= FEF50%), and MEF25 (= FEF75%).<br>
> **HSU_1979** and **WANG_1993** require an `ethnicity` argument.<br>
> **WANG_1993** currently implements the Male White subgroup only; other subgroups can be added to `wang_1993_coefficients.csv`.

### Lung diffusion capacity
| Class | Population | Publication |
|---|---|---|
| `GLI_2017` | Caucasian, age 5–80 y | Stanojevic et al. 2017, PMID: 28893868 |
| `SCAPIS_2023` | Swedish, age 50–65 y | Malinovschi et al. 2023, PMID: 37339507 |

### Static lung volumes
| Class | Population | Publication |
|---|---|---|
| `GLI_2021` | European ancestry, age 5–80 y | Hall et al. 2021, PMID: 33707167 |

### Oscillometry (IOS/FOT)
| Class | Population | Publication |
|---|---|---|
| `SCHULZ_2013` | KORA (German), adults | Schulz et al. 2013, PMID: 23691036 |

---

## Severity classifiers

| Class | Basis | Stages |
|---|---|---|
| `GOLD` | FEV1 % predicted (COPD) | I–IV (mild to very severe) |
| `STAR` | FEV1/FVC ratio (COPD) | I–IV (mild to very severe) |

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
| `compute(df, parameter, ...)` | Vectorised apply over a DataFrame; returns a DataFrame of metrics |

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

### LMS-based equations (GLI_2012, BOWERMANN_2022, GLI_2017, GLI_2021, SCAPIS_2023, KUBOTA_2014)

```python
from pyspiro import GLI_2012, BOWERMANN_2022

# Multi-ethnic equation — ethnicity_col required
gli = GLI_2012()
results = gli.compute(
    df,
    GLI_2012.Parameters.FEV1,
    value_col='fev1',
    ethnicity_col='eth',     # 1=Caucasian, 2=African-American, 3=NE Asian, 4=SE Asian
)
# DataFrame with columns: percent, zscore, lln, uln — same index as df
df[['fev1_pct', 'fev1_z', 'fev1_lln', 'fev1_uln']] = results

# Race-neutral — no ethnicity_col needed
bow = BOWERMANN_2022()
df[['fvc_pct', 'fvc_z', 'fvc_lln', 'fvc_uln']] = bow.compute(
    df, BOWERMANN_2022.Parameters.FVC, value_col='fvc')
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

bow = BOWERMANN_2022()
pct = bow.percent(1, 40, 175, BOWERMANN_2022.Parameters.FEV1, 3.2)  # no ethnicity

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
from pyspiro import GLI_2012, BOWERMANN_2022, HANKINSON_1999, compare_equations

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
    equations=[GLI_2012(), BOWERMANN_2022(), HANKINSON_1999()],
)
print(result)
```

```
         equation  percent_predicted    zscore  applicable
0        GLI_2012              71.12 -2.223992        True
1  BOWERMANN_2022              75.41 -1.685500        True
2  HANKINSON_1999                NaN       NaN       False
```

Pass `equations=None` to compare against all available equations automatically.

### Batch processing a cohort

```python
results = []
for _, row in df.iterrows():
    cmp = compare_equations(row, GLI_2012.Parameters.FEV1,
                            equations=[GLI_2012(), BOWERMANN_2022()])
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

Race-neutral equations (e.g. `BOWERMANN_2022`) do not require an ethnicity argument:

```python
from pyspiro import BOWERMANN_2022, plot_centile_curves

fig = plot_centile_curves(
    BOWERMANN_2022(),
    sex=1,
    height=175,
    parameter=BOWERMANN_2022.Parameters.FEV1,
)
```

---

## Planned future implementations

- **Spirometry** — Indian reference equations Northern Indian (Chhabra 2014, PMID: 25962195)
- **Spirometry** — Indian reference equations, Western Indian (Agarwal 2020, PMID: 32366494)
- **Spirometry** — Indian reference equations, Western Indian (Desai 2016, PMID: 27865240)
- **Spirometry** — Chinese reference equations (Jian 2017, PMID: 29268524)
- **Breath-washout** reference values

---

## Citation

If you use pyspiro in your research, please cite:

> Hendrik Pott, Roman Martin. pyspiro v0.4.0. doi:10.5281/zenodo.15519193
