from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd


class Quotient(ABC):
    """
    Abstract base class for physiological quotient implementations.

    A physiological quotient expresses a measured value as a multiple of a fixed
    1st percentile ("minimally survivable") value observed in a lung function
    population:

        Q = measured value / 1st percentile value

    Unlike a reference equation a quotient needs no age, height or ethnicity, and
    is still defined for patients an equation cannot score at all. For the same
    reason this is deliberately not a Reference subclass: there is no predicted
    median, no z-score and no limit of normal to take.

    Subclasses declare their published 1st percentiles as data and inherit
    percentile1(), quotient() and band():

        class MY_QUOTIENT(Quotient):
            class Parameters(Enum):
                FEV1 = 1
                FEV1FVC = 2

            _PERCENTILE_1_BY_SEX = {Parameters.FEV1.value: (0.40, 0.50)}
            _PERCENTILE_1_SEX_NEUTRAL = {Parameters.FEV1FVC.value: 0.15}
            _FRACTION_PARAMETERS = frozenset({Parameters.FEV1FVC.value})

    Only compute() is left abstract: the batch API differs between papers, since
    not every published index is a quotient.

    Argument conventions
    --------------------
    parameter : Parameters enum member (class-specific), or its integer value
    value     : the measured value, in the units of that parameter
    sex       : 0 = female, 1 = male; required only for sex-specific parameters
    """

    # {parameter value: (female, male)} — 1st percentiles that differ by sex
    _PERCENTILE_1_BY_SEX = {}

    # {parameter value: float} — 1st percentiles stable across sex as well as age
    _PERCENTILE_1_SEX_NEUTRAL = {}

    # Parameter values that must be given as a fraction (0-1), e.g. FEV1/FVC.
    # Values above 1 are rejected rather than silently rescaled, because a
    # genuine quotient can legitimately exceed 1.
    _FRACTION_PARAMETERS = frozenset()

    # Highest band band() will report
    MAX_BAND = 6

    _silent = True

    class Sex(Enum):
        FEMALE = 0
        MALE = 1

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_silence(self, silent: bool):
        """Suppress (True) or enable (False) input validation messages."""
        self._silent = silent

    def _warn(self, message: str):
        if not self._silent:
            print("%s: %s" % (type(self).__name__, message))

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _resolve_parameter(self, parameter):
        """Return the integer value of a Parameters member, or pd.NA if unknown."""
        try:
            return self.Parameters(getattr(parameter, "value", parameter)).value
        except ValueError:
            self._warn("unknown parameter %r; expected a Parameters member." % (parameter,))
            return pd.NA

    def _resolve_sex(self, sex):
        """Return 0/1, or pd.NA if the code is missing or unrecognised."""
        if sex is None or (not isinstance(sex, bool) and pd.isna(sex)):
            return pd.NA
        try:
            return self.Sex(int(getattr(sex, "value", sex))).value
        except (ValueError, TypeError):
            self._warn("sex must be 0 (female) or 1 (male), got %r." % (sex,))
            return pd.NA

    def _value_label(self, parameter) -> str:
        """Name used for the measured value in validation messages."""
        return "value"

    def _resolve_value(self, value, label: str = "value"):
        """Return a non-negative float, or pd.NA."""
        if value is None or pd.isna(value):
            return pd.NA
        try:
            value = float(value)
        except (TypeError, ValueError):
            self._warn("%s must be numeric, got %r." % (label, value))
            return pd.NA
        if value < 0:
            self._warn("%s must not be negative, got %.2f." % (label, value))
            return pd.NA
        return value

    @classmethod
    def parameter_for(cls, name: str):
        """
        Return the Parameters member matching a reference equation's parameter name.

        Falls back to the name with a 'Q' suffix, so an equation's FEV1 resolves to
        MILLER_2010.Parameters.FEV1Q. Returns None if nothing matches; names that
        differ beyond the suffix (GLI_2017 calls the SI transfer factor TLCO, the
        quotient calls it DLCO_SI) have to be bridged by the caller.
        """
        members = cls.Parameters.__members__
        return members.get(name) or members.get("%sQ" % name)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def is_sex_specific(self, parameter) -> bool:
        """Return True if the parameter has separate 1st percentiles by sex."""
        return self._resolve_parameter(parameter) in self._PERCENTILE_1_BY_SEX

    def percentile1(self, parameter, sex: int = None) -> float:
        """
        Return the 1st percentile value used as the denominator of Q.

        Parameters
        ----------
        parameter : Parameters member (or its integer value).
        sex       : 0 = female, 1 = male. Required for the sex-specific
                    parameters; ignored for the rest.

        Returns
        -------
        float, in the units of the requested parameter; pd.NA on invalid input,
        or where the parameter is not a quotient at all.
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            return pd.NA

        if param in self._PERCENTILE_1_SEX_NEUTRAL:
            return self._PERCENTILE_1_SEX_NEUTRAL[param]

        if param not in self._PERCENTILE_1_BY_SEX:
            self._warn("%s has no published 1st percentile."
                       % self.Parameters(param).name)
            return pd.NA

        code = self._resolve_sex(sex)
        if code is pd.NA:
            self._warn("%s has sex-specific 1st percentiles; pass sex=0 or sex=1."
                       % self.Parameters(param).name)
            return pd.NA
        return self._PERCENTILE_1_BY_SEX[param][code]

    def quotient(self, parameter, value: float, sex: int = None) -> float:
        """
        Return the physiological quotient Q = measured value / 1st percentile.

        A woman with an FEV1 of 1.20 L has an FEV1Q of 3.00 (1.20/0.40); the same
        value in a man gives 2.40 (1.20/0.50). Higher is better; Q=1 means the
        measurement sits at the minimally survivable value.

        Parameters
        ----------
        parameter : Parameters member (or its integer value).
        value     : the measured value, in the units of that parameter.
        sex       : 0 = female, 1 = male. Required for the sex-specific parameters.

        Returns
        -------
        float, rounded to 2 decimal places; pd.NA on invalid input.
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            return pd.NA

        value = self._resolve_value(value, self._value_label(param))
        if value is pd.NA:
            return pd.NA

        if param in self._FRACTION_PARAMETERS and value > 1:
            self._warn("%s must be a fraction (0-1), got %.2f; %.2f%% would be %.2f."
                       % (self.Parameters(param).name, value, value, value / 100))
            return pd.NA

        denominator = self.percentile1(param, sex)
        if denominator is pd.NA:
            return pd.NA
        return round(value / denominator, 2)

    def band(self, parameter, value: float, sex: int = None) -> int:
        """
        Return floor(Q), capped at MAX_BAND — the number of complete "turnovers"
        a measurement sits above the 1st percentile.

        0 means the measurement is at or below the 1st percentile. No severity
        labels are attached: none are published.

        Returns
        -------
        int in 0..MAX_BAND; pd.NA on invalid input.
        """
        q = self.quotient(parameter, value, sex)
        if q is pd.NA:
            return pd.NA
        return min(int(q), self.MAX_BAND)

    # ------------------------------------------------------------------
    # Batch API
    # ------------------------------------------------------------------

    @abstractmethod
    def compute(self, df: pd.DataFrame, parameter, value_col: str, **kwargs) -> pd.DataFrame:
        """Apply the quotient to every row of a DataFrame."""
        pass
