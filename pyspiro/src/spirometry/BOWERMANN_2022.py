from ..reference import SplineReference
from enum import Enum
import numpy
import pandas


class BOWERMANN_2022(SplineReference):
    """
    GLI 2022 race-neutral spirometry reference equations (Bowermann et al. 2023).

    Race-neutral Global Lung Function Initiative reference equations for
    spirometry. Designed to eliminate race-based correction factors. Covers
    both sexes across a broad age range.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: FEV1, FVC, FEV1/FVC.
    No ethnicity stratification (race-neutral design).

    Citation:
        Bowermann C, Bhakta NR, Brazzale D, et al. A Race-neutral Approach to
        the Interpretation of Lung Function Measurements. Am J Respir Crit Care
        Med. 2023;207(6):768-774. doi: 10.1164/rccm.202205-0963OC. PMID: 36383197.
    """

    _splines_csv = 'bowermann_2022_splines.csv'
    _coeffs_csv  = 'bowermann_2022_coefficients.csv'

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline, lspline = self._get_splines(sex, age, parameter)
        c = self._coefficients["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        if self.Parameters(parameter) in (self.Parameters.FEV1, self.Parameters.FVC):
            l = c.loc["q0"]
        else:
            l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age))

        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + sspline)

        return l, m, s
