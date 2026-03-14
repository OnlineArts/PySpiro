# pyspiro

![logo](https://github.com/OnlineArts/PySpiro/blob/main/pyspiro/data/pyspiro_250x.png?raw=true)

The Package pyspiro implements multiple spirometric, bodyplethysmographic and oscillometric lung function reference equations.

## Currently Available Models/Equations

- Standard and race-neutral **Spirometry** reference equations (GLI, LuftiBus): (Quanjer 2012, PMID: 22743675; Kuster 2008, PMID: 18057057, Bowerman 2023, PMID: 36383197)
- **Lung Diffusion** reference equations (GLI): (Stanojevic 2017, PMID: 28893868)
- **Lung Diffusion** reference equations (SCAPIS): (Malinovschi 2023, PMID: 37339507)
- **Static lung volumes** reference equations (GLI): (Hall 2021, PMID: 33707167)
- **Oscillometric** reference equations (KORA): (Schulz 2013, PMID: 23691036)

## Planned future implementations
- ECCS-1993 reference values (Laszlo 1993) (Version 1)
- Breath-washout reference values (version 2).

## Brief application example (2012 GLI reference equations)
```python
import pandas as pd
from pyspiro import GLI_2012

gli = GLI_2012()

# Suppose df is a pandas DataFrame object.
# sex_binary: 0 = female, 1 = male
# fev1 in liters, age in years, height in cm.
# Suppose patient ethinicity = Caucasian for all patients in dataset (here: "1")

df[['fev1_p', 'fev1_z', 'fev1_lln']] = df.apply(
    lambda x: pd.Series(
        gli.all(
            x.sex_binary,
            x.age,
            x.height,
            1, # Ethnicity
            gli.Parameters["FEV1"],
            x.fev1
        )
    ),
    axis=1
)
```

## If using, please cite as:
Hendrik Pott, Roman Martin. pySpiro: v.0.3.3. Published online Jun 10, 2025. doi:10.5281/zenodo.15519193
