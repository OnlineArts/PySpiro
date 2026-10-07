from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class CHERNIACK_1972(PredictedValueReference):
    """
    Cherniack (1972) spirometry reference equations.

    Cherniack, RM and Raber, MB: Normal Standards for Ventilatory Function
    Using an Automatic Wedge Spirometer.
    American Review of Respiratory Disease 1972; Vol 106(1), p38–46.

    Linear equations using height in inches. Input height is expected in cm and
    converted internally. MVV is in L/min; all other flows in L/sec.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF25 = 3
        FEF50 = 4
        FEF75 = 5
        FEF25_75 = 6
        PEFR = 7
        MVV = 8

    _AGE_RANGE = (15, 79)
    _HEIGHT_RANGE = (88.9, 215.9)   # 35–85 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'cherniack_1972_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age, na = self._validated(age, self._AGE_RANGE, 'age')
        height, na = self._validated(height, self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        height_in = height / 2.54
        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        return RegressionResult(float(row['a0']) + float(row['a_ht']) * height_in + float(row['a_age']) * age, na=na)
