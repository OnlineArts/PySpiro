from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas


class LOELOE_2025(Reference):
    """
    Iranian spirometry reference equations (Loeloe et al. 2025).

    Machine learning-based spirometry reference values for the Iranian population
    derived from the Shahedieh PERSIAN cohort using KNN regression. This implementation
    uses pre-computed lookup tables for predicted values (pv) and lower limits of
    normal (lln) based on the original study's calculator.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: FEV1, FVC, FEV1/FVC, FEF25-75.
    Age range: 38-69 years, Height range: 142-189 cm.
    Ethnicity: Not applicable (Iranian population specific).

    Lookup table format:
        pv  — predicted value (median); used for percent()
        lln — lower limit of normal (5th percentile)
    
    uln() is approximated as: 2 * pv - lln (95th percentile mirrored about the median).
    zscore() uses the normal approximation: (value − pv) / ((pv − lln) / 1.645).

    Citation:
        Loeloe MS, Sefidkar R, Tabatabaei SM, Mehrparvar AH and Jambarsang S (2025)
        Machine learning-based spirometry reference values for the Iranian population:
        a cross-sectional study from the Shahedieh PERSIAN cohort.
        Front. Med. 12:1480931. doi: 10.3389/fmed.2025.1480931

    Note: This implementation uses the pre-computed KNN-based reference values from
    the original study. Age and height are rounded to the nearest 0.1 unit before lookup,
    maintaining the original calculator's precision.
    """

    class Parameters(Enum):
        FEV1      = 1
        FVC       = 2
        FEV1FVC   = 3
        FEF25_75  = 4

    _AGE_RANGE    = (38.0, 69.0)
    _HEIGHT_RANGE = (142.0, 189.0)

    def __init__(self):
        self._lookup = self._load_lookup()
        self._age_range    = self._AGE_RANGE
        self._height_range = self._HEIGHT_RANGE

    def _load_lookup(self) -> pandas.DataFrame:
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'loeloe_2025_lookup.csv').open('rb') as f:
            df = pandas.read_csv(f, delimiter=';')
        df.set_index(['age', 'height'], inplace=True)
        return df

    def _get_pv_lln(self, sex: int, age: float, height: float, parameter: int):
        """Return (pv, lln) for rounded (age, height), or (pandas.NA, pandas.NA) if out of range."""
        # Round to the 0.1 grid resolution. Use round(x, 1) — not round(x / 0.1) * 0.1,
        # which reintroduces binary drift (185.1 -> 185.10000000000002) and misses the index.
        age_r = round(float(age), 1)
        ht_r  = round(float(height), 1)

        age_r = self.validate_range(age_r, self._AGE_RANGE, 'age')
        if age_r is pandas.NA:
            return pandas.NA, pandas.NA

        ht_r = self.validate_range(ht_r, self._HEIGHT_RANGE, 'height')
        if ht_r is pandas.NA:
            return pandas.NA, pandas.NA

        param_name = self.Parameters(parameter).name
        sex_label  = 'females' if sex == self.Sex.FEMALE.value else 'males'
        row = self._lookup.loc[(age_r, ht_r)]
        pv  = float(row[f'{param_name}_{sex_label}_pv'])
        lln = float(row[f'{param_name}_{sex_label}_lln'])
        # Some (age, height) cells exist for one sex only (e.g. tall females); those
        # are blank in the CSV and parse as NaN. Return NA so metrics short-circuit
        # consistently with out-of-range inputs.
        if pandas.isna(pv) or pandas.isna(lln):
            return pandas.NA, pandas.NA
        return pv, lln

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float = None) -> tuple:
        """Not applicable — LOELOE_2025 uses direct lookup, not LMS parameters."""
        return pandas.NA, pandas.NA, pandas.NA

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float) -> float:
        """Return measured value as % of the predicted median."""
        pv, _ = self._get_pv_lln(sex, age, height, parameter)
        return pandas.NA if pv is pandas.NA else round(value / pv * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float) -> float:
        """
        Return z-score: (value − pv) / ((pv − lln) / 1.645), normal approximation.
        
        This uses the standard relationship where LLN corresponds to -1.645 SD from the mean.
        """
        pv, lln = self._get_pv_lln(sex, age, height, parameter)
        if pv is pandas.NA:
            return pandas.NA
        see = (pv - lln) / 1.645
        return pandas.NA if see == 0 else (value - pv) / see

    def lln(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Return lower limit of normal (5th percentile)."""
        _, lln = self._get_pv_lln(sex, age, height, parameter)
        return lln

    def uln(self, sex: int, age: float, height: float, parameter: int) -> float:
        """
        Return upper limit of normal (95th percentile), approximated as 2 × pv − lln.
        This assumes symmetry around the median in the z-score scale.
        """
        pv, lln = self._get_pv_lln(sex, age, height, parameter)
        return pandas.NA if pv is pandas.NA else 2 * pv - lln

    def all(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return (percent, z-score, lln, uln) in a single call."""
        pv, lln = self._get_pv_lln(sex, age, height, parameter)
        if pv is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA, pandas.NA
        see = (pv - lln) / 1.645
        return (
            round(value / pv * 100, 2),
            (value - pv) / see if see != 0 else pandas.NA,
            lln,
            2 * pv - lln,
        )