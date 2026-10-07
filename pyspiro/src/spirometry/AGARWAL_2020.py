from ..reference import CentileLookupReference
from enum import Enum
import numpy


class AGARWAL_2020(CentileLookupReference):
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

    _lookup_csv = 'agarwal_2020_lookup.csv'
    _limit_suffix = 'p5'

    def _grid(self, value):
        # Integer grid: round half to even, as round() does
        if not isinstance(value, numpy.ndarray):
            return round(float(value))
        if numpy.isnan(value).any():
            raise ValueError("cannot convert float NaN to integer")    # as round(float(age))
        return numpy.rint(value).astype(numpy.int64)

    def _get_pv_p5(self, sex: int, age: float, height: float, parameter: int):
        """Return (pv, p5) for rounded (age, height), or (pandas.NA, pandas.NA) if out of range."""
        return self._pv_lln(sex, age, height, parameter)
