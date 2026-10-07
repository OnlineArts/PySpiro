from ..reference import PredictedValueReference, RegressionResult
from enum import Enum
import numpy


class KNUDSON_1983(PredictedValueReference):
    """
    Knudson (1983) spirometry reference equations.

    Knudson, Ronald J., et al.: Change in the Normal Maximum Expiratory
    Flow-Volume Curve with Growth and Aging.
    American Review of Respiratory Disease 1983; 127(5–6): 725–734.

    Subjects are stratified by sex and age group, each with its own linear
    (and occasionally quadratic) regression on height and age. FEV1/FVC
    expressed as a percentage.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEF50 = 3
        FEF75 = 4
        FEF25_75 = 5
        FEV1FVC = 6     # expressed as %

    _AGE_MALE_RANGE = (6, 90)
    _AGE_FEMALE_RANGE = (6, 88)

    # Height ranges are stratum-specific (PDF table p.37)
    _HEIGHT_RANGES = {
        'm_6_11':   (111.8, 154.9),  # 44–61 in
        'm_12_24':  (139.7, 193.0),  # 55–76 in
        'm_25plus': (157.5, 195.6),  # 62–77 in
        'f_6_10':   (106.7, 147.3),  # 42–58 in
        'f_11_19':  (132.1, 182.9),  # 52–72 in
        'f_20_69':  (147.3, 180.3),  # 58–71 in
        'f_70plus': (147.3, 167.6),  # 58–66 in
    }

    _age_range = (6, 90)
    _coeffs_csv = 'knudson_1983_coefficients.csv'
    _coeffs_index = ('parameter', 'sex', 'age_group')

    _ARRAY_REGRESSION = True

    def _age_group(self, sex: int, age):
        """Age stratum of the coefficient table; age may be a scalar or an array."""
        if isinstance(age, numpy.ndarray):
            if sex == self.Sex.MALE.value:
                return numpy.select([age <= 11, age <= 24], ['m_6_11', 'm_12_24'], 'm_25plus')
            return numpy.select([age <= 10, age <= 19, age <= 69], ['f_6_10', 'f_11_19', 'f_20_69'], 'f_70plus')
        if sex == self.Sex.MALE.value:
            if age <= 11:
                return 'm_6_11'
            elif age <= 24:
                return 'm_12_24'
            return 'm_25plus'
        else:
            if age <= 10:
                return 'f_6_10'
            elif age <= 19:
                return 'f_11_19'
            elif age <= 69:
                return 'f_20_69'
            return 'f_70plus'

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age, na = self._validated(age, age_range, 'age')
        if self._all_na(na):
            return RegressionResult.missing()

        def stratum(age_group, na, age, height):
            height, na = self._validated(height, self._HEIGHT_RANGES[age_group], 'height', na)
            if self._all_na(na):
                return RegressionResult.missing()
            row = self._row((param_name, sex_name, age_group))
            if row is None:
                return RegressionResult.missing()
            return RegressionResult(float(row['a0'])
                                    + float(row['a_ht']) * height
                                    + float(row['a_age']) * age
                                    + float(row['a_age2']) * age ** 2, na=na)

        return self._per_key(self._age_group(sex, age), na, stratum, age, height)
