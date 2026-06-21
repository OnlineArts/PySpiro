from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas


class AGARWAL_2020(Reference):
    """
    Western Indian spirometry reference equations (Agarwal et al. 2020).

    Reference values derived from 1,258 healthy adults in the Vadu Rural Health
    Programme, KEM Hospital Research Centre, Pune, Western India (ages 20–80 years).
    Models fitted using GAMLSS; predicted values and lower limits stored as
    pre-computed lookup tables indexed by age (integer years, 20–80) and height
    (integer cm, 137–185).

    Input age and height are rounded to the nearest integer before lookup.

    Lookup table columns (from supplementary material):
        pv  — predicted value (50th centile); used for percent()
        p5  — 5th centile; used as lln()
        lln — 2.5th centile (stored in the table but not returned by lln())

    uln() is approximated as 2 × pv − p5 (symmetric around the median).
    zscore() uses the normal approximation: (value − pv) / ((pv − p5) / 1.645).

    Variables: sex (0=female, 1=male), age (years, 20–80), height (cm, 137–185).
    Parameters: FEV1 (L), FVC (L), FEV1FVC (unitless ratio 0–1).
    No ethnicity stratification.

    Note: FEV1FVC is expressed as a unitless ratio (e.g. 0.82), consistent with
    GLI_2012 and most other modules in this package.

    Citation:
        Agarwal D, Parker RA, Pinnock H, Roy S, Ghorpade D, Salvi S,
        Khatavkar P, Juvekar S; RESPIRE collaboration. Normal spirometry
        predictive values for the Western Indian adult population.
        Eur Respir J. 2020;55(3):1902129.
        doi: 10.1183/13993003.02129-2019. PMID: 32366494.
    """

    class Parameters(Enum):
        FEV1    = 1
        FVC     = 2
        FEV1FVC = 3

    _AGE_RANGE    = (20, 80)
    _HEIGHT_RANGE = (137, 185)

    def __init__(self):
        self._lookup = self._load_lookup()
        self._age_range    = self._AGE_RANGE
        self._height_range = self._HEIGHT_RANGE

    def _load_lookup(self) -> pandas.DataFrame:
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'agarwal_2020_lookup.csv').open('rb') as f:
            df = pandas.read_csv(f, delimiter=';')
        df.set_index(['age', 'height'], inplace=True)
        return df

    def _get_pv_p5(self, sex: int, age: float, height: float, parameter: int):
        """Return (pv, p5) for rounded (age, height), or (pandas.NA, pandas.NA) if out of range."""
        age_i = round(float(age))
        ht_i  = round(float(height))

        age_i = self.validate_range(age_i, self._AGE_RANGE, 'age')
        if age_i is pandas.NA:
            return pandas.NA, pandas.NA

        ht_i = self.validate_range(ht_i, self._HEIGHT_RANGE, 'height')
        if ht_i is pandas.NA:
            return pandas.NA, pandas.NA

        param_name = self.Parameters(parameter).name
        sex_label  = 'females' if sex == self.Sex.FEMALE.value else 'males'
        row = self._lookup.loc[(age_i, ht_i)]
        pv  = float(row[f'{param_name}_{sex_label}_pv'])
        p5  = float(row[f'{param_name}_{sex_label}_p5'])
        return pv, p5

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float = None) -> tuple:
        """Not applicable — AGARWAL_2020 uses direct percentile lookup, not LMS."""
        return pandas.NA, pandas.NA, pandas.NA

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float) -> float:
        """Return measured value as % of the predicted median."""
        pv, _ = self._get_pv_p5(sex, age, height, parameter)
        return pandas.NA if pv is pandas.NA else round(value / pv * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float) -> float:
        """Return z-score: (value − pv) / ((pv − p5) / 1.645), normal approximation."""
        pv, p5 = self._get_pv_p5(sex, age, height, parameter)
        if pv is pandas.NA:
            return pandas.NA
        see = (pv - p5) / 1.645
        return pandas.NA if see == 0 else (value - pv) / see

    def lln(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Return lower limit of normal (5th centile)."""
        _, p5 = self._get_pv_p5(sex, age, height, parameter)
        return p5

    def uln(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Return upper limit of normal (95th centile), approximated as 2 × pv − p5."""
        pv, p5 = self._get_pv_p5(sex, age, height, parameter)
        return pandas.NA if pv is pandas.NA else 2 * pv - p5

    def all(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return (percent, z-score, lln, uln) in a single call."""
        pv, p5 = self._get_pv_p5(sex, age, height, parameter)
        if pv is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA, pandas.NA
        see = (pv - p5) / 1.645
        return (
            round(value / pv * 100, 2),
            (value - pv) / see if see != 0 else pandas.NA,
            p5,
            2 * pv - p5,
        )
