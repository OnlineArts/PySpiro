from ..reference import SplineReference
from enum import Enum
import numpy
import pandas


class ALQEREM_2021(SplineReference):
    """
    Al-Qerem 2021 spirometry reference equations for Middle Eastern children.

    GAMLSS/BCCG (Box-Cox Cole-Green) equations fitted to 1576 healthy Jordanian
    schoolchildren (870 males, 706 females) aged 6-18 years, recruited in Amman.
    The BCCG mu/sigma/nu parameterisation is identical to LMS: L = nu, M = mu,
    S = sigma, so the inherited percent/zscore/lln/uln apply unchanged.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: FEV1 (L), FVC (L), FEV1/FVC (%), FEF25-75 (L/s).

    Note that the cohort is Jordanian.  The paper's title says "a Middle Eastern
    population"; it is not an Iranian data set.

    Age is rounded to the nearest 0.25 y before the age-spline is looked up, as
    for the GLI equations.  Splines exist for males only, and only for FEV1,
    FEV1/FVC and FEF25-75 (Tables A3-A5); every other spline is zero.  The Lspline
    column is zero throughout, as published.

    Observed anthropometry in the fitting sample (not published as limits):
        males   height 104-194 cm, age 6.00-17.92 y
        females height 102-176 cm, age 6.08-17.92 y
    The age range enforced here is 6.00-17.75 y, the extent of the spline tables.
    The paper places no bounds on height and neither does this module, but the
    equations extrapolate poorly to age/height pairs the cohort never contained:
    at 17.75 y and 110 cm the predicted FEV1 exceeds the predicted FVC.

    Two published coefficients are corrected here.  Both were settled against the
    authors' own SPSS data set, whose stored predicted values reproduce every
    equation in Tables 2 and 3 to ~1e-5:

    1.  Table 2, FVC (males), prints "- 0.24743 * log (age)".  The sign must be
        positive.  As printed the equation returns an FVC below the FEV1 predicted
        by the same table (0.86 L vs 2.62 L at 150 cm / 12 y).  With +0.24743 the
        equation reproduces the authors' own predicted FVC exactly (residual 3e-14
        over all 870 males); with -0.24743 it is wrong by up to 4.8 L.

    2.  Table 2, FEV1/FVC (males), prints an intercept of 4.5057904.  Paired with
        the Table A4 age-spline this underestimates the authors' own predicted
        FEV1/FVC by a constant 0.104%.  Holding the two published slopes fixed,
        the intercept implied by their data is 4.5068298 (residual sd 1.8e-06),
        which is the value used here.  The intercept and the Mspline column are
        confounded up to an additive constant, so the published table A4 requires
        this intercept.

    The paper also prints the z-score as "(((Predicted value)^Nu) - 1)/(Nu * Sigma)",
    omitting the measured value.  The intended form is the standard BCCG one,
    ((measured/mu)^nu - 1)/(nu * sigma), which is what LMSReference implements and
    what reproduces the authors' stored z-scores exactly.

    Citation:
        Al-Qerem W. Spirometry reference equations for children from a Middle
        Eastern population. Int J Clin Pract. 2021;75(11):e14598.
        doi: 10.1111/ijcp.14598. PMID: 34216517.
    """

    _splines_csv = 'alqerem_2021_splines.csv'
    _coeffs_csv  = 'alqerem_2021_coefficients.csv'

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3
        FEF25_75 = 4

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet — that is (nu, mu, sigma) — for the given inputs."""
        if sex not in (0, 1):
            if not self._silent:
                print("ALQEREM_2021 sex must be 0 (female) or 1 (male).")
            return pandas.NA, pandas.NA, pandas.NA

        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline, lspline = self._get_splines(sex, age, parameter)
        c = self._coefficients[
            "%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())
        ]

        # FEV1/FVC in males is the one equation that takes height untransformed.
        h = numpy.log(height) if c.loc["h_log"] else height

        l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age)) + lspline
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * h) + (c.loc["a2"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + sspline)
        return l, m, s
