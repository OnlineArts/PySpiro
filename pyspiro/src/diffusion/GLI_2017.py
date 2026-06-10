from ..reference import SplineReference
from enum import Enum
import numpy
import pandas


class GLI_2017(SplineReference):
    """
    GLI 2017 lung diffusion capacity reference equations (Stanojevic et al. 2017).

    Global Lung Function Initiative reference equations for the carbon monoxide
    transfer factor in Caucasians. Covers both sexes, age range 5-80 years.
    This implementation uses the corrected 2020 erratum values.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: TLCO (SI), DLCO (traditional), KCO (SI), KCO (traditional), VA.
    No ethnicity stratification (Caucasian population only).

    Citation:
        Stanojevic S, Graham BL, Cooper BG, et al.; GLI TLCO working group.
        Official ERS technical standards: Global Lung Function Initiative
        reference values for the carbon monoxide transfer factor for Caucasians.
        Eur Respir J. 2017;50(3):1700010. doi: 10.1183/13993003.00010-2017.
        Erratum: Eur Respir J. 2020;56(4):1750010.
        doi: 10.1183/13993003.50010-2017. PMID: 28893868.
    """

    _splines_csv = 'gli_2017_splines.csv'
    _coeffs_csv  = 'gli_2017_coefficients.csv'

    class Parameters(Enum):
        TLCO = 1       # SI units (mmol/min/kPa)
        DLCO = 2       # Traditional units (mL/min/mmHg)
        KCO_SI = 3     # SI units (mmol/min/kPa/L)
        KCO_trad = 4   # Traditional units (mL/min/mmHg/L)
        VA = 5

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline, lspline = self._get_splines(sex, age, parameter)
        c = self._coefficients["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        l = c.loc["q0"]
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + sspline)

        return l, m, s
