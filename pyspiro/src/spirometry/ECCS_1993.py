from ..reference import PredictedValueReference, RegressionResult
from enum import Enum


class ECCS_1993(PredictedValueReference):
    """
    ECCS/ERS (Quanjer 1993) spirometry reference equations.

    Quanjer, Ph.H., et al.: Lung Volumes and Ventilatory Flows: Official Statement
    of the European Respiratory Society.
    European Respiratory Journal 1992–1993; Supplement 15–16: 5–40.

    Linear equations using height in cm and age in years. FEV1/FVC expressed as
    a percentage. Per the paper's note, for subjects aged 18–25 the predicted
    mean equals that for age 25. For males this applies to FEF75, FEF25_75,
    PEFR, and FIVC; for females it applies to all parameters.
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
        FIVC = 9

    _MALE_AGE_CLAMP_PARAMS = frozenset({'FEF75', 'FEF25_75', 'PEFR', 'FIVC'})
    _FEMALE_AGE_CLAMP_PARAMS = frozenset({
        'FVC', 'FEV1', 'FEV1FVC', 'FEF25', 'FEF50', 'FEF75', 'FEF25_75', 'PEFR', 'FIVC'
    })
    _FEF_AGE_MIN = 25

    _AGE_RANGE = (18, 70)
    _HEIGHT_MALE_RANGE = (155.0, 195.0)    # 61–76.8 in
    _HEIGHT_FEMALE_RANGE = (145.0, 180.0)  # 57.1–70.9 in

    _age_range = _AGE_RANGE
    _coeffs_csv = 'eccs_1993_coefficients.csv'
    _coeffs_index = ('parameter', 'sex')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()

        age, na = self._validated(age, self._AGE_RANGE, 'age')
        h_range = self._HEIGHT_MALE_RANGE if sex == self.Sex.MALE.value else self._HEIGHT_FEMALE_RANGE
        height, na = self._validated(height, h_range, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        clamp_params = self._MALE_AGE_CLAMP_PARAMS if sex == self.Sex.MALE.value else self._FEMALE_AGE_CLAMP_PARAMS
        effective_age = self._maximum(age, self._FEF_AGE_MIN) if param_name in clamp_params else age

        row = self._row((param_name, sex_name))
        if row is None:
            return RegressionResult.missing()

        return RegressionResult(float(row['a0']) + float(row['a_ht']) * height + float(row['a_age']) * effective_age, na=na)
