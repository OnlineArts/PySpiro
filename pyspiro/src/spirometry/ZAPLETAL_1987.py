from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class ZAPLETAL_1987(PredictedValueReference):
    """
    Zapletal (1987) spirometry reference equations for children and adolescents.

    Zapletal, A.: Lung Function in Children and Adolescents. Methods, Reference
    Values. Progress in Respiration Research Vol 22 (1987).

    Two formula types:
      power10 : predicted = 10^(a + b * log10(H[cm])) / divisor
                (divisor = 1000 converts mL→L or mL/min→L/min for volume params)
      linear  : predicted = a + b * H[cm]  (used for FEV1/FVC%)

    FVC, FEV1, SVC in L; FEF and PEFR in L/sec; MVV in L/min.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        FEF25 = 4
        FEF50 = 5
        FEF75 = 6
        FEF25_75 = 7
        PEFR = 8
        SVC = 9
        MVV = 10

    _AGE_RANGE = (6, 18)
    _HEIGHT_RANGE = (107.0, 182.0)    # 42.1–71.7 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'zapletal_1987_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age, na = self._validated(age, self._AGE_RANGE, 'age')
        height, na = self._validated(height, self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        if row['type'] == 'power10':
            return RegressionResult((10 ** (float(row['a']) + float(row['b']) * self._log10(height))) / float(row['divisor']), na=na)
        else:
            return RegressionResult(float(row['a']) + float(row['b']) * height, na=na)
