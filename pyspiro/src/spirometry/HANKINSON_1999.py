from ..reference import Reference
from enum import Enum
import importlib.resources
import pandas as pd


class HANKINSON_1999(Reference):
    """
    NHANES III spirometry reference equations (Hankinson et al. 1999).

    Derived from the Third National Health and Nutrition Examination Survey (NHANES III).
    Covers three US ethnic groups, two sexes, and two age ranges (children 8-19 y,
    adults 20-80 y).

    Two table structures from the paper are implemented via two separate CSV files:

    hankinson_1999_coefficients_t4_t5.csv  (Tables 4 & 5 — FVC, FEV1, FEV6, FEF25-75, PEF):
        Indexed by (parameter, sex, ethnicity, age_group); decimal separator: dot.
        Predicted = a0_pred + a1_age*Age + a2_age2*Age^2 + a3_ht2_pred*Ht(cm)^2
        LLN       = a0_pred + a1_age*Age + a2_age2*Age^2 + a3_ht2_lln *Ht(cm)^2
        (shared intercept and age terms; only the Ht^2 coefficient differs)

    hankinson_1999_coefficients_t6.csv  (Table 6 — FEV1/FVC%, FEV1/FEV6%):
        Indexed by (parameter, sex, ethnicity); decimal separator: dot. No age_group.
        Predicted = a0_pred + a1_age*Age
        LLN       = a0_lln  + a1_age*Age
        (shared age coefficient; only the intercept differs; no Ht or Age^2 terms)

    Derived quantities:
        SEE     = (Predicted - LLN) / 1.645
        ULN     = 2*Predicted - LLN      (symmetric 95th percentile)
        z-score = (observed - Predicted) / SEE

    Citation:
        Hankinson JL, Odencrantz JR, Fedan KB. Spirometric reference values from a
        sample of the general U.S. population. Am J Respir Crit Care Med.
        1999;159(1):179-187. doi: 10.1164/ajrccm.159.1.9712108. PMID: 9872837.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2
        FEV1FVC = 3     # FEV1/FVC expressed as % (Table 6)
        FEF25_75 = 4
        PEF = 5
        FEV1FEV6 = 6    # FEV1/FEV6 expressed as % (Table 6)
        FEV6 = 7        # FEV6 in litres (Tables 4 & 5)

    class Ethnicity(Enum):
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2
        MEXICAN_AMERICAN = 3

    _T4_T5_PARAMS = frozenset({'FVC', 'FEV1', 'FEV6', 'FEF25_75', 'PEF'})
    _T6_PARAMS    = frozenset({'FEV1FVC', 'FEV1FEV6'})

    # Male child range 8–19, female child range 8–17 (PDF table p.37)
    _CHILD_MAX_AGE_MALE   = 19
    _CHILD_MAX_AGE_FEMALE = 17
    _AGE_RANGE = (8, 80)

    # Height ranges per (sex, ethnicity, age_group) in cm (PDF table p.37)
    _HEIGHT_RANGES = {
        ('male',   'caucasian',        'child'): (122.0, 192.0),  # 48.0–75.6 in
        ('male',   'african_american', 'child'): (122.0, 194.0),  # 48.0–76.4 in
        ('male',   'mexican_american', 'child'): (120.0, 180.0),  # 47.2–70.9 in
        ('male',   'caucasian',        'adult'): (158.0, 194.0),  # 62.2–76.4 in
        ('male',   'african_american', 'adult'): (158.0, 196.0),  # 62.2–77.2 in
        ('male',   'mexican_american', 'adult'): (156.0, 192.0),  # 61.4–75.6 in
        ('female', 'caucasian',        'child'): (118.0, 178.0),  # 46.5–70.1 in
        ('female', 'african_american', 'child'): (118.0, 184.0),  # 46.5–72.4 in
        ('female', 'mexican_american', 'child'): (114.0, 172.0),  # 44.9–67.7 in
        ('female', 'caucasian',        'adult'): (145.0, 180.0),  # 57.1–70.9 in
        ('female', 'african_american', 'adult'): (146.0, 180.0),  # 57.5–70.9 in
        ('female', 'mexican_american', 'adult'): (136.0, 172.0),  # 53.5–67.7 in
    }

    def __init__(self):
        self._coeff_t45, self._coeff_t6 = self._load_coefficients()
        self._age_range = self._AGE_RANGE

    def _load_coefficients(self):
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'hankinson_1999_coefficients_t4_t5.csv').open('rb') as f:
            df_t45 = pd.read_csv(f, delimiter=";")
        df_t45.set_index(['parameter', 'sex', 'ethnicity', 'age_group'], inplace=True)

        with (pkg / 'hankinson_1999_coefficients_t6.csv').open('rb') as f:
            df_t6 = pd.read_csv(f, delimiter=";")
        df_t6.drop(columns=['R2'], errors='ignore', inplace=True)
        df_t6.set_index(['parameter', 'sex', 'ethnicity'], inplace=True)

        return df_t45, df_t6

    def _age_group(self, sex: int, age: float) -> str:
        threshold = self._CHILD_MAX_AGE_MALE if sex == self.Sex.MALE.value else self._CHILD_MAX_AGE_FEMALE
        return 'child' if age <= threshold else 'adult'

    def _compute(self, sex: int, age: float, height: float, ethnicity: int, parameter: int):
        """
        Return (predicted, lln) or (pd.NA, pd.NA) on failure.
        ULN = 2*predicted - lln; SEE = (predicted - lln) / 1.645.
        """
        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pd.NA:
            return pd.NA, pd.NA

        param_name = self.Parameters(parameter).name
        sex_name   = self.Sex(sex).name.lower()
        eth_name   = self.Ethnicity(ethnicity).name.lower()

        if param_name in self._T4_T5_PARAMS:
            age_group = self._age_group(sex, age)
            h_range = self._HEIGHT_RANGES.get((sex_name, eth_name, age_group))
            if h_range is None:
                return pd.NA, pd.NA
            height = self.validate_range(height, h_range, 'height')
            if height is pd.NA:
                return pd.NA, pd.NA
            try:
                row = self._coeff_t45.loc[(param_name, sex_name, eth_name, age_group)]
            except KeyError:
                if not self._silent:
                    print(
                        f"HANKINSON_1999: no coefficients for "
                        f"({param_name}, {sex_name}, {eth_name}, {age_group})"
                    )
                return pd.NA, pd.NA

            ht2  = height ** 2
            base = (float(row['a0_pred'])
                    + float(row['a1_age'])  * age
                    + float(row['a2_age2']) * age ** 2)
            pred    = base + float(row['a3_ht2_pred']) * ht2
            lln_val = base + float(row['a3_ht2_lln'])  * ht2

        elif param_name in self._T6_PARAMS:
            try:
                row = self._coeff_t6.loc[(param_name, sex_name, eth_name)]
            except KeyError:
                if not self._silent:
                    print(
                        f"HANKINSON_1999: no coefficients for "
                        f"({param_name}, {sex_name}, {eth_name})"
                    )
                return pd.NA, pd.NA

            age_term = float(row['a1_age']) * age
            pred     = float(row['a0_pred']) + age_term
            lln_val  = float(row['a0_lln'])  + age_term

        else:
            return pd.NA, pd.NA

        return pred, lln_val

    # ── Abstract method implementations ────────────────────────────────────────

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        """
        Return (l=1, m=predicted, s=SEE/m) for base-class formula compatibility.
        With l=1: z = (value-m)/SEE, LLN = m - 1.645*SEE, ULN = m + 1.645*SEE.
        """
        pred, lln_val = self._compute(sex, age, height, ethnicity, parameter)
        if pred is pd.NA or pred == lln_val:
            return pd.NA, pd.NA, pd.NA
        see = (pred - lln_val) / 1.645
        return 1.0, pred, see / pred

    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return % of predicted."""
        pred, _ = self._compute(sex, age, height, ethnicity, parameter)
        return pd.NA if pred is pd.NA else round(value / pred * 100, 2)

    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return z-score: (observed - predicted) / SEE."""
        pred, lln_val = self._compute(sex, age, height, ethnicity, parameter)
        if pred is pd.NA or pred == lln_val:
            return pd.NA
        return (value - pred) / ((pred - lln_val) / 1.645)

    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return LLN (5th percentile) directly from the paper's LLN equation."""
        _, lln_val = self._compute(sex, age, height, ethnicity, parameter)
        return lln_val

    def uln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return ULN (95th percentile): 2*Predicted - LLN (symmetric around predicted)."""
        pred, lln_val = self._compute(sex, age, height, ethnicity, parameter)
        return pd.NA if pred is pd.NA else 2.0 * pred - lln_val

    def all(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return (percent, z-score, lln, uln) in a single call."""
        pred, lln_val = self._compute(sex, age, height, ethnicity, parameter)
        if pred is pd.NA:
            return pd.NA, pd.NA, pd.NA, pd.NA
        see = (pred - lln_val) / 1.645 if pred != lln_val else 0
        return (
            round(value / pred * 100, 2),
            (value - pred) / see if see != 0 else pd.NA,
            lln_val,
            2.0 * pred - lln_val,
        )
