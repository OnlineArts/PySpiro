from enum import Enum

import pandas as pd

from .quotient import Quotient


class MILLER_2010(Quotient):
    """
    FEV1 quotient and height-standardised FEV1 indices (Miller & Pedersen 2010).

    The paper that introduced the physiological quotient. Miller and Pedersen
    analysed 26 967 subjects -- Copenhagen City Heart Study (n=13 900), a COPD
    cohort (n=1095) and hospital lung function patients (n=11 972) -- and proposed
    two ways of expressing FEV1 that avoid reference equations entirely:

    FEV1Q -- the FEV1 quotient
        FEV1 divided by a sex-specific 1st percentile ("the number of turnovers of
        a nominal lower limit of lung function remaining"). The 1st percentile was
        0.50 L in males and 0.40 L in females, and did not vary significantly with
        age above 50 years, where the estimates were most reliable.

    FEV1.Ht^-3 and FEV1.Ht^-2 -- height-standardised FEV1
        FEV1 divided by height in metres cubed or squared. Standardising by body
        size rather than by a predicted value. The authors concluded that "standard-
        isation by Ht cubed is better than using lower powers of Ht"; FEV1.Ht^-3 was
        the second-best mortality predictor after FEV1Q, ahead of both % predicted
        and the standardised residual.

    Height is passed in cm, following the rest of this package, and converted to
    metres internally -- Miller's indices are defined on metres, so a 1.76 m
    subject with an FEV1 of 0.67 L has FEV1.Ht^-3 = 0.12, not 1.2e-7.

    Relationship to KNOX_BROWN_2026
    -------------------------------
    The FEV1Q denominators here are the same 0.50 / 0.40 L that KNOX-BROWN et al.
    independently reproduced in 2026 and extended to FVC, FEV1/FVC, DLCO, KCO, VA
    and TLC. For anything other than FEV1, and for batch work across parameters,
    use [KNOX_BROWN_2026]; this class exists for the original derivation and for
    the height-standardised indices, which no later paper carries. The two give
    identical FEV1Q values, but neither derives its percentiles from the other:
    both are Quotient subclasses declaring their own published tables, so a
    correction to one cannot silently move the other.

    No normative range is published for the height-standardised indices
    ------------------------------------------------------------------
    Miller and Pedersen report no predicted value, LLN, centile or z-score for
    FEV1.Ht^-3 or FEV1.Ht^-2. In the paper these indices are interpreted solely
    through the survival analysis, which this class deliberately does not
    implement (see below). ``height_standardised()`` therefore returns a bare
    number with nothing in this package to say whether it is normal or abnormal.
    Treat it as a size-corrected magnitude for comparison within a cohort, not as
    a clinical index in its own right.

    Survival prediction is deliberately not implemented
    --------------------------------------------------
    The paper's table 6 gives polynomial coefficients predicting lower quartile,
    median and upper quartile survival in years from FEV1Q or FEV1.Ht^-3. Those
    are out of scope here by design. They also do not reconcile with the paper's
    own worked examples: applied to the seven FEV1Q values in table 7, the
    published median-survival coefficients (1.71 + 1.08Q + 0.49Q^2) over-predict
    every one of them, by +1.0 years at Q=1.34 rising to +3.6 years at Q=7.50.
    A quadratic refitted to table 7 reproduces it to within 0.02 years, so table 7
    was computed from some other polynomial. The discrepancy cannot be resolved
    from the published text, and only the median row can be checked at all --
    table 7 reports no quartiles. Anyone tempted to add survival prediction later
    should resolve that first.

    Citation:
        Miller MR, Pedersen OF. New concepts for expressing forced expiratory
        volume in 1 s arising from survival analysis.
        Eur Respir J 2010;35(4):873-882. doi: 10.1183/09031936.00110809
    """

    class Parameters(Enum):
        FEV1Q = 1        # FEV1 / sex-specific 1st percentile
        FEV1_HT3 = 2     # FEV1 / height(m)^3 -- the authors' preferred power
        FEV1_HT2 = 3     # FEV1 / height(m)^2

    # 1st percentile of FEV1 in litres: (female, male), from figure 2.
    # The height-standardised indices are not quotients and have no denominator.
    _PERCENTILE_1_BY_SEX = {Parameters.FEV1Q.value: (0.40, 0.50)}

    _HEIGHT_POWERS = {
        Parameters.FEV1_HT3.value: 3,
        Parameters.FEV1_HT2.value: 2,
    }

    def _value_label(self, parameter) -> str:
        return "FEV1"

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    #
    # percentile1(), quotient() and band() are inherited from Quotient.  Only
    # FEV1Q has a 1st percentile: percentile1() and quotient() return pd.NA for
    # FEV1_HT3 and FEV1_HT2, which are reached through height_standardised().
    #
    # Miller and Pedersen note that within a single sex FEV1Q is a constant
    # rescaling of FEV1 and so "has no advantage over raw FEV1" -- its value is in
    # making measurements comparable across sexes without a reference equation.

    def height_standardised(self, fev1: float, height: float, power: int = 3) -> float:
        """
        Return FEV1 divided by height in metres raised to ``power``.

        Parameters
        ----------
        fev1   : measured FEV1 in litres.
        height : height in cm (converted to metres internally).
        power  : 3 for FEV1.Ht^-3 (the authors' preferred index) or 2 for
                 FEV1.Ht^-2. Default 3.

        Returns
        -------
        float rounded to 4 decimal places, or pd.NA on invalid input. There is no
        published normative range for this index -- see the class docstring.

        Examples
        --------
        >>> MILLER_2010().height_standardised(0.67, 176.0)
        0.1229
        """
        if power not in (2, 3):
            self._warn("power must be 2 or 3, got %r." % (power,))
            return pd.NA

        fev1 = self._resolve_value(fev1, "FEV1")
        if fev1 is pd.NA:
            return pd.NA

        if height is None or pd.isna(height):
            return pd.NA
        try:
            height = float(height)
        except (TypeError, ValueError):
            self._warn("height must be numeric, got %r." % (height,))
            return pd.NA
        if height <= 0:
            self._warn("height must be positive, got %.1f." % height)
            return pd.NA

        return round(fev1 / (height / 100.0) ** power, 4)

    # ------------------------------------------------------------------
    # Batch API
    # ------------------------------------------------------------------

    def compute(self, df: pd.DataFrame, parameter, value_col: str = 'FEV1',
                sex_col: str = 'sex', height_col: str = 'height') -> pd.DataFrame:
        """
        Apply one of Miller's indices to every row of a DataFrame.

        Parameters
        ----------
        df         : DataFrame with one patient per row.
        parameter  : Parameters member (or its integer value).
        value_col  : column holding the measured FEV1 in litres. Default 'FEV1'.
        sex_col    : column for sex (0=female, 1=male). Read only for FEV1Q.
        height_col : column for height in cm. Read only for the height-standardised
                     indices.

        Returns
        -------
        DataFrame indexed like df with a single column named after the parameter.

        Examples
        --------
        >>> miller = MILLER_2010()
        >>> df['FEV1Q'] = miller.compute(df, MILLER_2010.Parameters.FEV1Q)['FEV1Q']
        >>> df['FEV1_HT3'] = miller.compute(
        ...     df, MILLER_2010.Parameters.FEV1_HT3)['FEV1_HT3']
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            raise ValueError("MILLER_2010.compute: unknown parameter %r." % (parameter,))

        if value_col is None:
            raise ValueError(
                "MILLER_2010.compute: a measured FEV1 is required; "
                "pass value_col='<column_name>'."
            )

        name = self.Parameters(param).name

        if param == self.Parameters.FEV1Q.value:
            if sex_col is None:
                raise ValueError(
                    "MILLER_2010.compute: FEV1Q is sex-specific; "
                    "pass sex_col='<column_name>'."
                )
            series = df.apply(
                lambda r: self.quotient(param, r[value_col], r[sex_col]), axis=1)
        else:
            if height_col is None:
                raise ValueError(
                    "MILLER_2010.compute: %s requires height; "
                    "pass height_col='<column_name>'." % name
                )
            power = self._HEIGHT_POWERS[param]
            series = df.apply(
                lambda r: self.height_standardised(r[value_col], r[height_col], power),
                axis=1)

        return pd.DataFrame({name: series}, index=df.index)
