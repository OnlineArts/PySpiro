import math
from enum import Enum

import pandas

from ..reference import Reference


class CALOGERO_2013(Reference):
    """
    Pediatric oscillometry reference equations (Calogero et al. 2013).

    Provides predicted values, z-scores, LLN, and ULN for respiratory
    oscillometry (FOT) parameters in healthy children aged 2.7–12.9 years.
    Derived from 760 healthy Caucasian children (335 male, 425 female) at
    two sites (Perth, Australia and Viterbo, Italy).

    Device: I2M pseudo-random noise oscillometer (Chess Medical / Cosmed);
    frequencies 4–48 Hz. Parameters reported at 6, 8, and 10 Hz.

    Predictors: height (cm) and sex (0=female, 1=male).
    Age has no significant independent effect once height is included.
    Height range: 92–159 cm (approximately 2.7–12.9 years).

    Parameters and units:
        Rrs6, Rrs8, Rrs10  — respiratory system resistance  (hPa·s·L⁻¹)
        Xrs6, Xrs8, Xrs10  — respiratory system reactance   (hPa·s·L⁻¹; typically negative)
        AX                 — area under the reactance curve  (hPa·L⁻¹)
        Fres               — resonant frequency              (Hz)

    Transformations used to linearise residuals (Table 2):
        Rrs  : natural log — predicted_log = a + b_sex × sex + b_ht × height
        Xrs  : √(10 − Xrs) — T = a + b_sex × sex + b_ht × height
        AX   : √AX
        Fres : untransformed

    Z-score formula (all parameters on transformed scale):
        z = (T(measured) − T(predicted)) / SEE
    A positive z-score means the measured value is worse than predicted
    (higher Rrs, more negative Xrs, higher AX, higher Fres).

    LLN / ULN correspond to the 5th and 95th percentiles on the original
    clinical scale, derived by transforming T ± 1.645 × SEE back to clinical
    units.  For Xrs, a more negative value is the lower (5th-percentile, LLN)
    end; the uln() result is the least negative normal value.

    percent() is defined for Rrs, AX, and Fres (measured / predicted × 100).
    It is not defined for Xrs (signed values make the ratio ambiguous) and
    returns pd.NA.

    lms() returns (NA, NA, NA) — this is not an LMS equation.

    Note on Fdep (frequency dependence of resistance): height-category ranges
    are published in the paper (< 140 cm: 0.04–0.27 hPa·s²·L⁻¹;
    ≥ 140 cm: 0.02–0.24 hPa·s²·L⁻¹) but no regression equation exists;
    Fdep is therefore not included as a Parameter.

    Note on Hellinckx et al. 2001 (Eur Respir J 2001;17:564-570): that paper
    compares IOS and FOT in 49 mixed patients and contains no normative
    reference equations; it is therefore not implemented as a module.

    Citation:
        Calogero C, Simpson SJ, Lombardi E, Parri N, Cuomo B, Palumbo M,
        de Martino M, Shackleton C, Verheggen M, Gavidia T, Franklin PJ,
        Kusel MM, Hall GL.
        Respiratory impedance and bronchodilator responsiveness in healthy
        children aged 2–13 years.
        Pediatr Pulmonol. 2013;48(7):707–715.
        doi: 10.1002/ppul.22680. PMID: 22961800.
    """

    class Parameters(Enum):
        Rrs6  = 1
        Rrs8  = 2
        Rrs10 = 3
        Xrs6  = 4
        Xrs8  = 5
        Xrs10 = 6
        AX    = 7
        Fres  = 8

    _HEIGHT_RANGE = (92.0, 159.0)

    # (intercept, sex_coef, height_coef, SEE)  — Table 2, Calogero 2013
    # Sex: 0 = female, 1 = male (consistent with pyspiro convention)
    # Fres has no significant sex term (0.0 used as placeholder)
    _COEFFS = {
        1:  (3.37377, -0.04157, -0.01155, 0.223),   # Rrs6
        2:  (3.44422, -0.03942, -0.01228, 0.213),   # Rrs8
        3:  (3.40885, -0.03211, -0.01248, 0.202),   # Rrs10
        4:  (4.23244, -0.03134, -0.00537, 0.137),   # Xrs6
        5:  (4.06745, -0.03243, -0.00463, 0.133),   # Xrs8
        6:  (4.08552, -0.02565, -0.00494, 0.138),   # Xrs10
        7:  (11.90851, -0.32673, -0.05518, 1.432),  # AX
        8:  (45.68724,  0.0,    -0.17763, 5.147),   # Fres
    }

    _RRS_PARAMS = frozenset({1, 2, 3})
    _XRS_PARAMS = frozenset({4, 5, 6})

    def _predict_transformed(self, sex: int, height: float, parameter: int) -> tuple:
        """Return (T_predicted, SEE) on the transformed scale."""
        c = self._COEFFS[parameter]
        T = c[0] + c[1] * int(sex) + c[2] * float(height)
        return T, c[3]

    def _p(self, parameter) -> int:
        """Normalise parameter to integer value (accepts int or Parameters enum)."""
        return self.Parameters(parameter).value

    def _forward(self, value: float, p: int) -> float:
        """Transform a measured value to the regression scale."""
        v = float(value)
        if p in self._RRS_PARAMS:
            return math.log(v)
        if p in self._XRS_PARAMS:
            return math.sqrt(10.0 - v)   # v < 10 always physiologically
        if p == 7:                        # AX
            return math.sqrt(v)
        return v                          # Fres: identity

    def _back(self, T: float, p: int) -> float:
        """Back-transform from regression scale to clinical units."""
        if p in self._RRS_PARAMS:
            return math.exp(T)
        if p in self._XRS_PARAMS:
            return 10.0 - T * T
        if p == 7:                        # AX
            return max(0.0, T * T)
        return T                          # Fres: identity

    def _validate(self, height: float) -> float:
        return self.validate_range(float(height), self._HEIGHT_RANGE, 'height')

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    def lms(self, sex: int, age: float, height: float, parameter,
            value: float = None) -> tuple:
        """Not applicable — CALOGERO_2013 uses direct regression, not LMS."""
        return pandas.NA, pandas.NA, pandas.NA

    def percent(self, sex: int, age: float, height: float, parameter,
                value: float) -> float:
        """
        Return measured value as % of predicted.

        Not defined for Xrs parameters (signed values); returns pd.NA.
        """
        p = self._p(parameter)
        if p in self._XRS_PARAMS:
            return pandas.NA
        height = self._validate(height)
        if height is pandas.NA:
            return pandas.NA
        T_pred, _ = self._predict_transformed(sex, height, p)
        predicted = self._back(T_pred, p)
        return round(float(value) / predicted * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter,
               value: float) -> float:
        """
        Return z-score on the transformed scale: (T(measured) − T(predicted)) / SEE.

        Positive z means worse than predicted for all parameters
        (higher Rrs / more negative Xrs / higher AX / higher Fres).
        """
        p = self._p(parameter)
        height = self._validate(height)
        if height is pandas.NA:
            return pandas.NA
        T_pred, see = self._predict_transformed(sex, height, p)
        T_meas = self._forward(float(value), p)
        return round((T_meas - T_pred) / see, 4)

    def lln(self, sex: int, age: float, height: float, parameter) -> float:
        """
        Return lower limit of normal (5th percentile on the clinical scale).

        For Rrs, AX, Fres: the 5th percentile is the smaller value
        (T_pred − 1.645 × SEE back-transformed).
        For Xrs: the 5th percentile is the most negative value
        (T_pred + 1.645 × SEE back-transformed, since √(10−Xrs) increases
        as Xrs becomes more negative).
        """
        p = self._p(parameter)
        height = self._validate(height)
        if height is pandas.NA:
            return pandas.NA
        T_pred, see = self._predict_transformed(sex, height, p)
        if p in self._XRS_PARAMS:
            return round(self._back(T_pred + 1.645 * see, p), 4)
        return round(self._back(T_pred - 1.645 * see, p), 4)

    def uln(self, sex: int, age: float, height: float, parameter) -> float:
        """
        Return upper limit of normal (95th percentile on the clinical scale).

        For Rrs, AX, Fres: the 95th percentile is the larger value.
        For Xrs: the 95th percentile is the least negative value.
        """
        p = self._p(parameter)
        height = self._validate(height)
        if height is pandas.NA:
            return pandas.NA
        T_pred, see = self._predict_transformed(sex, height, p)
        if p in self._XRS_PARAMS:
            return round(self._back(T_pred - 1.645 * see, p), 4)
        return round(self._back(T_pred + 1.645 * see, p), 4)

    def predicted(self, sex: int, age: float, height: float, parameter) -> float:
        """Return the predicted median value (50th percentile)."""
        p = self._p(parameter)
        height = self._validate(height)
        if height is pandas.NA:
            return pandas.NA
        T_pred, _ = self._predict_transformed(sex, height, p)
        return round(self._back(T_pred, p), 4)
