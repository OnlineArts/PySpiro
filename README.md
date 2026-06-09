# pyspiro

![logo](https://github.com/OnlineArts/PySpiro/blob/main/pyspiro/data/pyspiro_250x.png?raw=true)

**pyspiro** is a Python package implementing lung function reference equations for spirometry, static lung volumes, diffusion capacity, and oscillometry. It provides predicted values, z-scores, % predicted, lower limits of normal (LLN), and upper limits of normal (ULN) for research and clinical data analysis pipelines.

---

## Available reference equations

### Spirometry
| Class | Population | Publication |
|---|---|---|
| `GLI_2012` | Multi-ethnic, age 3–95 y | Quanjer et al. 2012, PMID: 22743675 |
| `BOWERMANN_2022` | Race-neutral (GLI global), age 3–95 y | Bowermann et al. 2023, PMID: 36383197 |
| `KUSTER_2008` | Swiss LuftiBus, age 18–80 y | Kuster et al. 2008, PMID: 18057057 |
| `HANKINSON_1999` | NHANES III (US), age 8–80 y | Hankinson et al. 1999, PMID: 9872837 |
| `KUBOTA_2014` | JRS (Japanese), age 17–95 y | Kubota et al. 2014, PMID: 25278192 |

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

All LMS-based equation classes expose a consistent API:

| Method | Returns |
|---|---|
| `percent(...)` | Measured value as % of predicted median |
| `zscore(...)` | Z-score relative to the reference distribution |
| `lln(...)` | Lower limit of normal (5th percentile) |
| `uln(...)` | Upper limit of normal (95th percentile) |
| `lms(...)` | Raw (L, M, S) triplet |
| `all(...)` | Tuple of (% predicted, z-score, LLN) or (% predicted, z-score, LLN, ULN) |

**Conventions**: sex as integer (0 = female, 1 = male); age in years; height in cm; measured values in their natural units (L, L/s, mmol/min/kPa, etc.). FEV1/FVC ratios are passed as a fraction (0–1) for LMS-based equations.

---

## Installation

```bash
pip install pyspiro
```

---

## Usage examples

### LMS-based equations (GLI, Bowermann, SCAPIS, Kubota)

```python
import pandas as pd
from pyspiro import GLI_2012

gli = GLI_2012()

# sex: 0 = female, 1 = male | height in cm | fev1 in litres | ethnicity: 1 = Caucasian
df[['fev1_pct', 'fev1_z', 'fev1_lln']] = df.apply(
    lambda x: pd.Series(
        gli.all(x.sex, x.age, x.height, 1, gli.Parameters.FEV1, x.fev1)
    ),
    axis=1
)

# ULN is available as a separate call for all equation sets
df['fev1_uln'] = df.apply(
    lambda x: gli.uln(x.sex, x.age, x.height, 1, gli.Parameters.FEV1, x.fev1),
    axis=1
)
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
from pyspiro import GLI_2012, GOLD
import pandas as pd

gli = GLI_2012()
gold = GOLD()

df['fev1_pct'] = df.apply(
    lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters.FEV1, x.fev1),
    axis=1
)
df['GOLD'] = df.apply(lambda x: gold.classify(FEV1p=x.fev1_pct), axis=1)
df['GOLD'] = pd.Categorical(df['GOLD'], categories=gold.get_order(), ordered=True)
```

---

## Planned future implementations

- **Spirometry** — ECCS 1993 (Laszlo 1993)
- **Spirometry** — South Korean KNHANES IV (Jo 2018, PMID: 29215803)
- **Spirometry** — Indian reference equations (Chhabra 2014, PMID: 25962195)
- **Spirometry** — Indian reference equations, Western Indian (Agarwal 2020, PMID: 32366494)
- **Spirometry** — Indian reference equations, Western Indian (Desai 2016, PMID: 27865240)
- **Spirometry** — Chinese reference equations (Jian 2017, PMID: 29268524)
- **Breath-washout** reference values

---

## Citation

If you use pyspiro in your research, please cite:

> Hendrik Pott, Roman Martin. pyspiro v0.4.0. doi:10.5281/zenodo.15519193
