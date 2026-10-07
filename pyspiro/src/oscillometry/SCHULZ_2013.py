from ..reference import RegressionReference, RegressionResult
from enum import Enum
import importlib.resources
import numpy
import pandas


class SCHULZ_2013(RegressionReference):
    """
    KORA oscillometry reference equations (Schulz et al. 2013).

    Reference values for impulse oscillometry system (IOS/FOT) parameters
    derived from adults of advanced age in the KORA study. Uses a linear
    regression model (not LMS-based); outputs are the 5th, 50th, and 95th
    percentiles directly. ULN = 95th percentile, LLN = 5th percentile.

    Variables: sex (0=female, 1=male), age (years), height (cm), weight (kg).
    Parameters: respiratory resistance R10, R15, R25, R35;
                reactance X10, X20, X25, X35.

    Note: percent() and zscore() are not applicable to this equation set and
    return None. Use percentiles(), lln(), or uln() instead.

    Citation:
        Schulz H, Flexeder C, Behr J, et al.; KORA Study Group. Reference
        values of impulse oscillometric lung function indices in adults of
        advanced age. PLoS One. 2013;8(5):e63366.
        doi: 10.1371/journal.pone.0063366. PMID: 23691036.
    """

    class Parameters(Enum):
        R10 = 1
        R15 = 2
        R25 = 3
        R35 = 4
        X10 = 5
        X20 = 6
        X25 = 7
        X35 = 8

    def __init__(self):
        self.__lookup = self.__load_lookup_table()

    def __load_lookup_table(self) -> pandas.DataFrame:
        with (importlib.resources.files('pyspiro.data') / 'schulz_2013_splines.csv').open('rb') as f:
            splines = pandas.read_csv(f, delimiter=";").set_index("Var")
        return splines

    def __get_regression_coeffs(self, sex: int, pct: float, parameter: int):
        for i in ("intercept", "age", "height", "weight"):
            yield self.__lookup["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())].loc["%s_%s" % (i, pct)]

    _SCALAR_TYPE = numpy.float64
    _ARRAY_REGRESSION = True
    # percent() and zscore() are not defined (they return None); compute() calls them per row
    _VECTORISED_METRICS = ('lln', 'uln')

    def _percentile(self, sex: int, pct: float, parameter: int, age, height, weight):
        intercept, age_coeff, height_coeff, weight_coeff = self.__get_regression_coeffs(sex, pct=pct, parameter=parameter)
        weight_coeff = 0 if pandas.isna(weight_coeff) else weight_coeff
        return intercept + (age_coeff * age) + (height_coeff * height) + (weight_coeff * weight)

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        if age is pandas.NA or sex is pandas.NA or height is pandas.NA or weight is pandas.NA:
            return RegressionResult.missing()
        p5 = self._percentile(sex, 0.05, parameter, age, height, weight)
        p50 = self._percentile(sex, 0.50, parameter, age, height, weight)
        p95 = self._percentile(sex, 0.95, parameter, age, height, weight)
        return RegressionResult(p50, lln=p5, uln=p95)

    def percentiles(self, sex: int, age: float, height: float, weight: float, parameter: int) -> tuple:
        """Return the (5th, 50th, 95th) percentile values."""
        r = self._regression(sex, age, height, None, weight, parameter)
        if r.na:
            return pandas.NA, pandas.NA, pandas.NA
        return r.lln, r.pred, r.uln

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Not applicable — SCHULZ_2013 uses direct percentile regression, not LMS."""
        pass

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Not applicable — use percentiles() instead."""
        pass

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Not applicable — use percentiles() instead."""
        pass

    def lln(self, sex: int, age: float, height: float, weight: float, parameter: int, value: float):
        """Return lower limit of normal (5th percentile)."""
        p5, p50, p95 = self.percentiles(sex, age, height, weight, parameter)
        return pandas.NA if (p5 is pandas.NA or p50 is pandas.NA or p95 is pandas.NA) else p5

    def uln(self, sex: int, age: float, height: float, weight: float, parameter: int, value: float):
        """Return upper limit of normal (95th percentile)."""
        p5, p50, p95 = self.percentiles(sex, age, height, weight, parameter)
        return pandas.NA if (p5 is pandas.NA or p50 is pandas.NA or p95 is pandas.NA) else p95

    def all(self, sex: int, age: float, height: float, weight: float, parameter: int, value: float):
        """Return (lln, median, uln) — i.e. (5th, 50th, 95th percentile) — in a single call."""
        p5, p50, p95 = self.percentiles(sex, age, height, weight, parameter)
        if (p5 is pandas.NA or p50 is pandas.NA or p95 is pandas.NA):
            return pandas.NA, pandas.NA, pandas.NA
        else:
            return p5, p50, p95