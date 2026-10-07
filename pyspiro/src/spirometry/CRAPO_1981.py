from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class CRAPO_1981(PredictedValueReference):
    """
    Crapo (1981) spirometry reference equations.

    Crapo, et al.: Reference Spirometric Values using Techniques and Equipment
    that Meet ATS Recommendations.
    American Review of Respiratory Disease 1981; 123: 659–664.

    Linear equations using height in cm and age in years.
    FEV1/FVC and FEV3/FVC expressed as percentages.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV05 = 2
        FEV1 = 3
        FEV3 = 4
        FEF25_75 = 5
        FEV1FVC = 6     # expressed as %
        FEV3FVC = 7     # expressed as %

    _AGE_MALE_RANGE = (15, 91)
    _AGE_FEMALE_RANGE = (17, 84)
    _HEIGHT_MALE_RANGE = (157.0, 194.0)    # 61.8–76.4 in
    _HEIGHT_FEMALE_RANGE = (146.0, 178.0)  # 57.5–70.1 in

    _age_range = (15, 91)
    _coeffs_csv = 'crapo_1981_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        male = sex == self.Sex.MALE.value
        age, na = self._validated(age, self._AGE_MALE_RANGE if male else self._AGE_FEMALE_RANGE, 'age')
        height, na = self._validated(height, self._HEIGHT_MALE_RANGE if male else self._HEIGHT_FEMALE_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        return RegressionResult(float(row['a0']) + float(row['a_ht']) * height + float(row['a_age']) * age, na=na)
