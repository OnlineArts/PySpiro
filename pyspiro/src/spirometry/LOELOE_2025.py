from ..reference import CentileLookupReference
from enum import Enum
import numpy


class LOELOE_2025(CentileLookupReference):
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

    _lookup_csv = 'loeloe_2025_lookup.csv'
    _limit_suffix = 'lln'
    # Some (age, height) cells exist for one sex only (e.g. tall females); those
    # are blank in the CSV and parse as NaN. Return NA so metrics short-circuit
    # consistently with out-of-range inputs.
    _EMPTY_CELLS_NA = True

    def _grid(self, value):
        # Round to the 0.1 grid resolution. Use round(x, 1) — not round(x / 0.1) * 0.1,
        # which reintroduces binary drift (185.1 -> 185.10000000000002) and misses the index.
        if not isinstance(value, numpy.ndarray):
            return round(float(value), 1)
        return numpy.array([round(v, 1) for v in numpy.asarray(value, dtype=float).tolist()])

    def _get_pv_lln(self, sex: int, age: float, height: float, parameter: int):
        """Return (pv, lln) for rounded (age, height), or (pandas.NA, pandas.NA) if out of range."""
        return self._pv_lln(sex, age, height, parameter)
