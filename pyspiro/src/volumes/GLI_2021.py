from ..reference import SplineReference
from enum import Enum
import numpy
import pandas


class GLI_2021(SplineReference):
    """
    GLI 2021 static lung volume reference equations (Hall et al. 2021).

    Global Lung Function Initiative reference equations for static lung volumes
    in individuals of European ancestry. Covers both sexes, age range 5-80 years.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: FRC, TLC, RV, RV/TLC, ERV, IC, VC.
    No ethnicity stratification (European ancestry only).

    Units: absolute volumes (FRC, TLC, RV, ERV, IC, VC) are in litres; RV/TLC
    is modelled as a percentage (~15-45), so a measured ratio must be supplied
    as a percentage (e.g. 35), not a fraction (0.35).

    Citation:
        Hall GL, Filipow N, Ruppel G, et al.; GLI Network members. Official ERS
        technical standard: Global Lung Function Initiative reference values for
        static lung volumes in individuals of European ancestry. Eur Respir J.
        2021;57(3):2000289. doi: 10.1183/13993003.00289-2020. PMID: 33707167.
    """

    _splines_csv = 'gli_2021_splines.csv'
    _coeffs_csv  = 'gli_2021_coefficients.csv'

    class Parameters(Enum):
        FRC = 1
        TLC = 2
        RV = 3
        RV_TLC = 4
        ERV = 5
        IC = 6
        VC = 7

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline, lspline = self._get_splines(sex, age, parameter)
        c = self._coefficients["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]
        param = self.Parameters(parameter)

        a0, a1, a2 = float(c.loc["a0"]), float(c.loc["a1"]), float(c.loc["a2"])
        p0, p1 = float(c.loc["p0"]), float(c.loc["p1"])

        # Hall 2021 (table 3) does NOT use a single functional form for every
        # index. a1 is always the age coefficient, a2 the height coefficient,
        # but the predictors are log-transformed for some parameters and left
        # linear for others:
        #   FRC, TLC     : M = a0 + a1*log(age) + a2*log(height) + Mspline
        #   RV, RV/TLC   : M = a0 + a1*age      + a2*height       + Mspline
        #   ERV, IC, VC  : M = a0 + a1*age      + a2*log(height)  + Mspline
        if param in (self.Parameters.FRC, self.Parameters.TLC):
            m_age, m_height = numpy.log(age), numpy.log(height)
        elif param in (self.Parameters.RV, self.Parameters.RV_TLC):
            m_age, m_height = age, height
        else:  # ERV, IC, VC
            m_age, m_height = age, numpy.log(height)

        m = numpy.exp(a0 + (a1 * m_age) + (a2 * m_height) + mspline)

        # S equation (table 3): FRC uses log(age); every other index uses
        # linear age. Only FRC/TLC/RV/RV_TLC carry an age-varying Sspline.
        #   FRC              : S = p0 + p1*log(age) + Sspline
        #   TLC, RV, RV/TLC  : S = p0 + p1*age      + Sspline
        #   ERV, IC, VC      : S = p0 + p1*age
        s_age = numpy.log(age) if param is self.Parameters.FRC else age
        if param in (self.Parameters.FRC, self.Parameters.TLC,
                     self.Parameters.RV, self.Parameters.RV_TLC):
            s = numpy.exp(p0 + (p1 * s_age) + sspline)
        else:
            s = numpy.exp(p0 + (p1 * s_age))

        l = float(c.loc["q0"])

        return l, m, s
