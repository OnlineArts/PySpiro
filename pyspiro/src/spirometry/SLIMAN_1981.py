from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas


class SLIMAN_1981(Reference):
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

    def __init__(self):
        self._coefficients = self._load_coefficients()
        self._age_range    = self._AGE_RANGE
        self._height_range = self._HEIGHT_RANGE

    def _load_coefficients(self) -> pandas.DataFrame:
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'sliman_1981_coefficients.csv').open('rb') as f:
            df = pandas.read_csv(f, delimiter=';')
        return df.set_index(['sex', 'parameter'])

    def _predicted_sd(self, sex: int, age: float, height: float, parameter: int):
        """Return (predicted, sd) or (pandas.NA, pandas.NA) if out of range."""
        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pandas.NA:
            return pandas.NA, pandas.NA
        height = self.validate_range(height, self._HEIGHT_RANGE, 'height')
        if height is pandas.NA:
            return pandas.NA, pandas.NA

        param_name = self.Parameters(parameter).name
        row = self._coefficients.loc[(int(sex), param_name)]
        predicted = (
            float(row['height_coef']) * float(height)
            + float(row['age_coef']) * float(age)
            + float(row['intercept'])
        )
        return predicted, float(row['sd'])

    def lms(self, sex, age, height, parameter=None, value=None):
        """Not applicable — SLIMAN_1981 is a linear regression, not an LMS model."""
        return pandas.NA, pandas.NA, pandas.NA

    def percent(self, sex, age, height, parameter=None, value=None):
        """Return measured value as % of the predicted value."""
        pred, _ = self._predicted_sd(sex, age, height, parameter)
        return pandas.NA if pred is pandas.NA else round(value / pred * 100, 2)

    def zscore(self, sex, age, height, parameter=None, value=None):
        """Return z-score: (value - predicted) / SD."""
        pred, sd = self._predicted_sd(sex, age, height, parameter)
        if pred is pandas.NA:
            return pandas.NA
        return (value - pred) / sd

    def lln(self, sex, age, height, parameter=None):
        """Return lower limit of normal (predicted - 1.645 * SD)."""
        pred, sd = self._predicted_sd(sex, age, height, parameter)
        return pandas.NA if pred is pandas.NA else pred - 1.645 * sd

    def uln(self, sex, age, height, parameter=None):
        """Return upper limit of normal (predicted + 1.645 * SD)."""
        pred, sd = self._predicted_sd(sex, age, height, parameter)
        return pandas.NA if pred is pandas.NA else pred + 1.645 * sd

    def predicted(self, sex, age, height, parameter=None):
        """Return the predicted value for the given inputs."""
        pred, _ = self._predicted_sd(sex, age, height, parameter)
        return pred
