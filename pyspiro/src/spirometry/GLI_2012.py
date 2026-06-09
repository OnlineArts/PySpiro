from ..reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class GLI_2012(Reference):
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

    def __init__(self):
        self.__lookup, self.__splines = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        lookup_path = importlib.resources.open_binary('pyspiro.data', 'gli_2012_splines.csv')
        splines_path = importlib.resources.open_binary('pyspiro.data', 'gli_2012_coefficients.csv')
        lookup = pandas.read_csv(lookup_path, delimiter=";").set_index("age")
        splines = pandas.read_csv(splines_path, delimiter=";").set_index("var")
        self._age_range: tuple = (min(lookup.index), max(lookup.index))
        return lookup, splines

    def __get_splines(self, sex: int, age: float, parameter: int):
        for i in ("Sspline", "Mspline", "Lspline"):
            yield self.__lookup["%s_%ss_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower(), i)].loc[age]

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age",)
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline, lspline = self.__get_splines(sex, age, parameter)
        c = self.__splines["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        AfrAm = int(ethnicity == self.Ethnicity["AFRICAN_AMERICAN"].value)
        NEAsia = int(ethnicity == self.Ethnicity["NORTHEAST_ASIAN"].value)
        SEAsia = int(ethnicity == self.Ethnicity["SOUTHEAST_ASIAN"].value)

        l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age)) + lspline
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + (c.loc["a3"] * AfrAm) + (c.loc["a4"] * NEAsia) + (c.loc["a5"] * SEAsia) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + (c.loc["p2"] * AfrAm) + (c.loc["p3"] * NEAsia) + (c.loc["p4"] * SEAsia) + sspline)

        return l, m, s

    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return % of predicted."""
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else round(( value / m ) * 100, 2)

    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return z-score."""
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else (((value/m)**l) - 1) / (l * s)

    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return lower limit of normal (5th percentile)."""
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))

    def uln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return upper limit of normal (95th percentile)."""
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m))

    def all(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return (percent, z-score, lln) in a single call."""
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        if (l is pandas.NA or m is pandas.NA or s is pandas.NA):
            return pandas.NA
        else:
            return round(( value / m ) * 100, 2), (((value/m)**l) - 1) / (l * s), numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))
