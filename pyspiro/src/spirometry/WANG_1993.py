from ..reference import PredictedValueReference, RegressionResult
from enum import Enum
import numpy


class WANG_1993(PredictedValueReference):
    """
    Wang (1993) spirometry reference equations for children and adolescents.

    Wang, Xiaobin, et al.: Pulmonary Function Between 6 and 18 Years of Age.
    Pediatric Pulmonology 1993; 15: 75–88.

    Formula: predicted = exp(alpha + beta * ln(H[m]))
    where alpha and beta are looked up from an age-indexed table (integer age).
    FEV1/FVC is returned as a percentage (decimal result × 100).
    FEF25–75% is not available for ages 6–7.

    Currently only Male White coefficients are implemented (from the casestudy
    reference table). Other subgroups (Male Black, Female White, Female Black)
    should be added to wang_1993_coefficients.csv from the original paper.
    No LLN published; lln(), uln(), and zscore() return pd.NA.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # expressed as %
        FEF25_75 = 4

    class Ethnicity(Enum):
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2

    _AGE_MALE_RANGE = (6, 18)
    _AGE_FEMALE_RANGE = (7, 18)

    # Height ranges vary by ethnicity: African-American minimum is 120 cm (PDF p.37)
    _HEIGHT_RANGES = {
        ('male',   'caucasian'):        (110.0, 190.0),  # 43.3–74.8 in
        ('male',   'african_american'): (120.0, 190.0),  # 47.2–74.8 in
        ('female', 'caucasian'):        (110.0, 180.0),  # 43.3–70.9 in
        ('female', 'african_american'): (120.0, 180.0),  # 47.2–70.9 in
    }

    _PARAM_COLS = {
        'FVC':     ('fvc_alpha',     'fvc_beta'),
        'FEV1':    ('fev1_alpha',    'fev1_beta'),
        'FEV1FVC': ('fev1fvc_alpha', 'fev1fvc_beta'),
        'FEF25_75':('fef25_75_alpha','fef25_75_beta'),
    }

    _age_range = (6, 18)
    _coeffs_csv = 'wang_1993_coefficients.csv'
    _coeffs_index = ('sex', 'ethnicity', 'age')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        param_name = self.Parameters(parameter).name
        sex_name = self.Sex(sex).name.lower()
        eth_name = self.Ethnicity(ethnicity).name.lower()

        age_range = self._AGE_MALE_RANGE if sex == self.Sex.MALE.value else self._AGE_FEMALE_RANGE
        age, na = self._validated(age, age_range, 'age')
        if self._all_na(na):
            return RegressionResult.missing()

        h_range = self._HEIGHT_RANGES.get((sex_name, eth_name))
        if h_range is None:
            return RegressionResult.missing()
        height, na = self._validated(height, h_range, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        alpha_col, beta_col = self._PARAM_COLS[param_name]

        def whole_year(age_int, na, height):
            # Coefficients are tabulated per whole year of age
            row = self._row((sex_name, eth_name, age_int))
            if row is None:
                return RegressionResult.missing()
            alpha = row[alpha_col]
            beta = row[beta_col]
            if numpy.isnan(alpha) or numpy.isnan(beta):
                return RegressionResult.missing()
            height_m = height / 100.0
            result = self._exp(float(alpha) + float(beta) * self._log(height_m))
            if param_name == 'FEV1FVC':
                result *= 100.0
            return RegressionResult(result, na=na)

        age_int = numpy.trunc(age).astype(int) if isinstance(age, numpy.ndarray) else int(age)
        return self._per_key(age_int, na, whole_year, height)
