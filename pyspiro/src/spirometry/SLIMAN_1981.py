from ..reference import RegressionReference, RegressionResult
from enum import Enum
import pandas


class SLIMAN_1981(RegressionReference):
    """
    Jordanian spirometry reference equations (Sliman, Dajani & Dajani 1981).

    Multiple linear regression equations for FVC, FEV1 and FMF (FEF25-75) derived
    from 261 healthy non-smoking adult Jordanians (144 men, 117 women) aged 20-60
    years, tested in Amman with a Vitalograph dry bellows spirometer (BTPS
    corrected). This is the "old" Jordanian reference, superseded for most uses by
    the GAMLSS-based ALQEREM_2019 equations, but retained for historical comparison.

    Equation form (height in cm, age in years):
        predicted = height_coef * height + age_coef * age + intercept

    The published residual standard deviation (SD) is used to derive limits and
    z-scores under a normal-error assumption:
        zscore = (value - predicted) / SD
        lln    = predicted - 1.645 * SD   (one-sided 5th percentile)
        uln    = predicted + 1.645 * SD   (one-sided 95th percentile)

    Variables: sex (0=female, 1=male), age (years, 20-60), height (cm, 140-190).
    Parameters: FVC (L), FEV1 (L), FEF25_75 (L/s, reported in the paper as FMF 25-75%).
    No ethnicity stratification.

    Coefficients are stored in sliman_1981_coefficients.csv (Results section of
    the original publication). The paper reports nomograms rather than worked
    numeric examples, so no per-subject example values are published.

    Citation:
        Sliman NA, Dajani BM, Dajani HM. Ventilatory function test values of
        healthy adult Jordanians. Thorax. 1981;36(7):546-549.
        doi: 10.1136/thx.36.7.546. PMID: 7314041.
    """

    class Parameters(Enum):
        FVC      = 1
        FEV1     = 2
        FEF25_75 = 3   # reported in the paper as FMF 25-75%

    _AGE_RANGE    = (20, 60)
    _HEIGHT_RANGE = (140, 190)

    _age_range = _AGE_RANGE
    _height_range = _HEIGHT_RANGE

    _coeffs_csv = 'sliman_1981_coefficients.csv'
    _coeffs_index = ('sex', 'parameter')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        age, na = self._validated(age, self._AGE_RANGE, 'age')
        height, na = self._validated(height, self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        param_name = self.Parameters(parameter).name
        row = self._row((int(sex), param_name), required=True)
        predicted = (
            float(row['height_coef']) * height
            + float(row['age_coef']) * age
            + float(row['intercept'])
        )
        sd = float(row['sd'])
        return RegressionResult(predicted, lln=predicted - 1.645 * sd, uln=predicted + 1.645 * sd,
                                center=predicted, scale=sd, na=na)

    def lms(self, sex, age, height, parameter=None, value=None):
        """Not applicable — SLIMAN_1981 is a linear regression, not an LMS model."""
        return pandas.NA, pandas.NA, pandas.NA

    def percent(self, sex, age, height, parameter=None, value=None):
        """Return measured value as % of the predicted value."""
        return self._percent(self._scalar_regression(sex, age, height, None, None, parameter), value)

    def zscore(self, sex, age, height, parameter=None, value=None):
        """Return z-score: (value - predicted) / SD."""
        return self._zscore(self._scalar_regression(sex, age, height, None, None, parameter), value)

    def lln(self, sex, age, height, parameter=None):
        """Return lower limit of normal (predicted - 1.645 * SD)."""
        return self._lln(self._scalar_regression(sex, age, height, None, None, parameter))

    def uln(self, sex, age, height, parameter=None):
        """Return upper limit of normal (predicted + 1.645 * SD)."""
        return self._uln(self._scalar_regression(sex, age, height, None, None, parameter))

    def predicted(self, sex, age, height, parameter=None):
        """Return the predicted value for the given inputs."""
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        return pandas.NA if r is None else r.pred
