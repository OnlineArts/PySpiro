from ..reference import SplineReference
from enum import Enum
import numpy
import pandas


class GLI_2012(SplineReference):
    """
    GLI 2012 multi-ethnic spirometry reference equations (Quanjer et al. 2012).

    Global Lung Function Initiative reference equations for spirometry covering
    four ethnic groups, both sexes, and an age range of 3-95 years.

    Variables: sex (0=female, 1=male), age (years), height (cm), ethnicity.
    Parameters: FEV1, FVC, FEV1/FVC, FEF25-75, FEF75, FEV0.75, FEV0.75/FVC.
    Ethnicity: Caucasian (1), African-American (2), NE Asian (3), SE Asian (4).

    Citation:
        Quanjer PH, Stanojevic S, Cole TJ, et al.; ERS Global Lung Function
        Initiative. Multi-ethnic reference values for spirometry for the 3-95-yr
        age range: the global lung function 2012 equations. Eur Respir J.
        2012;40(6):1324-43. doi: 10.1183/09031936.00080312. PMID: 22743675.
    """

    _splines_csv = 'gli_2012_splines.csv'
    _coeffs_csv  = 'gli_2012_coefficients.csv'

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3
        FEF25_75 = 4
        FEF75 = 5
        FEV075 = 6
        FEV075FVC = 7

    class Ethnicity(Enum):
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2
        NORTHEAST_ASIAN = 3
        SOUTHEAST_ASIAN = 4

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline, lspline = self._get_splines(sex, age, parameter)
        c = self._coefficients["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        AfrAm = int(ethnicity == self.Ethnicity["AFRICAN_AMERICAN"].value)
        NEAsia = int(ethnicity == self.Ethnicity["NORTHEAST_ASIAN"].value)
        SEAsia = int(ethnicity == self.Ethnicity["SOUTHEAST_ASIAN"].value)

        l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age)) + lspline
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + (c.loc["a3"] * AfrAm) + (c.loc["a4"] * NEAsia) + (c.loc["a5"] * SEAsia) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + (c.loc["p2"] * AfrAm) + (c.loc["p3"] * NEAsia) + (c.loc["p4"] * SEAsia) + sspline)

        return l, m, s
