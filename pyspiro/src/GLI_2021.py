from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class GLI_2021(Reference):
    """
    GLI 2021 static lung volume reference equations (Hall et al. 2021).

    Global Lung Function Initiative reference equations for static lung volumes
    in individuals of European ancestry. Covers both sexes, age range 5-80 years.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: FRC, TLC, RV, RV/TLC, ERV, IC, VC.
    No ethnicity stratification (European ancestry only).

    Citation:
        Hall GL, Filipow N, Ruppel G, et al.; GLI Network members. Official ERS
        technical standard: Global Lung Function Initiative reference values for
        static lung volumes in individuals of European ancestry. Eur Respir J.
        2021;57(3):2000289. doi: 10.1183/13993003.00289-2020. PMID: 33707167.
    """

    class Parameters(Enum):
        FRC = 1
        TLC = 2
        RV = 3
        RV_TLC = 4
        ERV = 5
        IC = 6
        VC = 7

    def __init__(self):
        self.__lookup, self.__splines = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        lookup_path = importlib.resources.open_binary('pyspiro.data', 'gli_2021_splines.csv')
        splines_path = importlib.resources.open_binary('pyspiro.data', 'gli_2021_coefficients.csv')
        lookup = pandas.read_csv(lookup_path, delimiter=";").set_index("age")
        splines = pandas.read_csv(splines_path, delimiter=";").set_index("var")
        self._age_range: tuple = (min(lookup.index), max(lookup.index))
        return lookup, splines

    def __get_splines(self, sex: int, age: float, parameter: int):
        for i in ("Sspline", "Mspline", "Lspline"):
            yield self.__lookup["%s_%ss_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower(), i)].loc[age]

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA
        sspline, mspline, lspline = self.__get_splines(sex, age, parameter)
        c = self.__splines["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]
        
        if self.Parameters(parameter).name in ['FRC', 'TLC', 'RV', 'RV_TLC']:
            s = numpy.exp(float(c.loc["p0"]) + (float(c.loc["p1"]) * numpy.log(age)) + sspline)
        elif self.Parameters(parameter).name in ['ERV', 'IC', 'VC']:
            s = numpy.exp(float(c.loc["p0"]) + (float(c.loc["p1"]) * numpy.log(age)))

        m = numpy.exp(float(c.loc["a0"]) + (float(c.loc["a1"]) * numpy.log(height)) + (float(c.loc["a2"]) * numpy.log(age)) + mspline)
        l = float(c.loc["q0"])

        return l, m, s

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return % of predicted."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else round(( value / m ) * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return z-score."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else (((value/m)**l) - 1) / (l * s)

    def lln(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return lower limit of normal (5th percentile)."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))

    def uln(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return upper limit of normal (95th percentile)."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m))

    def all(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return (percent, z-score, lln) in a single call."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        if (l is pandas.NA or m is pandas.NA or s is pandas.NA):
            return pandas.NA
        else:
            return round(( value / m ) * 100, 2), (((value/m)**l) - 1) / (l * s), numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))