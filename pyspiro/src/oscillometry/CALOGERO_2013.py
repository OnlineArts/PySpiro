import math
from enum import Enum

import numpy
import pandas

from ..reference import RegressionReference, RegressionResult, _metric_column


class CALOGERO_2013(RegressionReference):
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

    def _predict_transformed(self, sex: int, height, parameter: int) -> tuple:
        """Return (T_predicted, SEE) on the transformed scale; height may be an array."""
        c = self._COEFFS[parameter]
        T = c[0] + c[1] * int(sex) + c[2] * (height if isinstance(height, numpy.ndarray) else float(height))
        return T, c[3]

    def _p(self, parameter) -> int:
        """Normalise parameter to integer value (accepts int or Parameters enum)."""
        return self.Parameters(parameter).value

    def _forward(self, value, p: int):
        """Transform a measured value (scalar or array) to the regression scale."""
        if numpy.ndim(value):
            if p in self._RRS_PARAMS:
                return numpy.log(value)
            if p in self._XRS_PARAMS:
                return numpy.sqrt(10.0 - value)
            if p == 7:
                return numpy.sqrt(value)
            return value
        v = float(value)
        if p in self._RRS_PARAMS:
            return math.log(v)
        if p in self._XRS_PARAMS:
            return math.sqrt(10.0 - v)   # v < 10 always physiologically
        if p == 7:                        # AX
            return math.sqrt(v)
        return v                          # Fres: identity

    def _back(self, T, p: int):
        """Back-transform from regression scale to clinical units; T may be an array."""
        if numpy.ndim(T):
            if p in self._RRS_PARAMS:
                return numpy.exp(T)
            if p in self._XRS_PARAMS:
                return 10.0 - T * T
            if p == 7:
                return numpy.maximum(0.0, T * T)
            return T
        if p in self._RRS_PARAMS:
            return math.exp(T)
        if p in self._XRS_PARAMS:
            return 10.0 - T * T
        if p == 7:                        # AX
            return max(0.0, T * T)
        return T                          # Fres: identity

    @staticmethod
    def _round(x, digits: int):
        """Python's round() on a scalar or on each element of an array."""
        if numpy.ndim(x):
            return numpy.array([round(v, digits) for v in x.tolist()], dtype=float)
        return round(x, digits)

    def _validate(self, height: float) -> float:
        return self.validate_range(float(height), self._HEIGHT_RANGE, 'height')

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        p = self._p(parameter)
        height, na = self._validated(height if isinstance(height, numpy.ndarray) else float(height),
                                     self._HEIGHT_RANGE, 'height')
        if self._all_na(na):
            return RegressionResult.missing()
        T_pred, see = self._predict_transformed(sex, height, p)
        # For Xrs the 5th percentile is the most negative value: T_pred + 1.645 x SEE back-transformed
        xrs = p in self._XRS_PARAMS
        lower = T_pred + 1.645 * see if xrs else T_pred - 1.645 * see
        upper = T_pred - 1.645 * see if xrs else T_pred + 1.645 * see
        return RegressionResult(
            None if xrs else self._back(T_pred, p),       # % predicted is not defined for Xrs
            lln=self._round(self._back(lower, p), 4),
            uln=self._round(self._back(upper, p), 4),
            center=T_pred, scale=see, na=na,
            predicted=self._round(self._back(T_pred, p), 4), transform=p)

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
        if self._p(parameter) in self._XRS_PARAMS:
            return pandas.NA
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        if r is None:
            return pandas.NA
        return round(float(value) / r.pred * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter,
               value: float) -> float:
        """
        Return z-score on the transformed scale: (T(measured) − T(predicted)) / SEE.

        Positive z means worse than predicted for all parameters
        (higher Rrs / more negative Xrs / higher AX / higher Fres).
        """
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        if r is None:
            return pandas.NA
        T_meas = self._forward(float(value), r.transform)
        return round((T_meas - r.center) / r.scale, 4)

    def lln(self, sex: int, age: float, height: float, parameter) -> float:
        """
        Return lower limit of normal (5th percentile on the clinical scale).

        For Rrs, AX, Fres: the 5th percentile is the smaller value
        (T_pred − 1.645 × SEE back-transformed).
        For Xrs: the 5th percentile is the most negative value
        (T_pred + 1.645 × SEE back-transformed, since √(10−Xrs) increases
        as Xrs becomes more negative).
        """
        return self._lln(self._scalar_regression(sex, age, height, None, None, parameter))

    def uln(self, sex: int, age: float, height: float, parameter) -> float:
        """
        Return upper limit of normal (95th percentile on the clinical scale).

        For Rrs, AX, Fres: the 95th percentile is the larger value.
        For Xrs: the 95th percentile is the least negative value.
        """
        return self._uln(self._scalar_regression(sex, age, height, None, None, parameter))

    def predicted(self, sex: int, age: float, height: float, parameter) -> float:
        """Return the predicted median value (50th percentile)."""
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        return pandas.NA if r is None else r.predicted

    def _metric_from_arrays(self, metric, merged, value, index):
        if metric != 'zscore':
            return super()._metric_from_arrays(metric, merged, value, index)
        na = merged.na
        if na.all():
            return _metric_column(numpy.full(merged.n, numpy.nan), na, index)
        r = merged.result()
        valid = ~na
        p = int(r.transform[valid][0])
        v = value[valid]
        # math.log / math.sqrt raise outside their domain: leave those inputs to the row-wise path
        if ((p in self._RRS_PARAMS and (v <= 0).any()) or (p in self._XRS_PARAMS and (v > 10.0).any())
                or (p == 7 and (v < 0).any())):
            return None
        with numpy.errstate(all="ignore"):
            T_meas = self._forward(numpy.where(valid, value, 1.0), p)
            values = self._round((T_meas - r.center) / r.scale, 4)
        return _metric_column(values, na, index)
