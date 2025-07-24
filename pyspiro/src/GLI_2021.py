from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class GLI_2021(Reference):
    """
    This global lung function was published in 2021 by Hall and colleagues and includes as variable sex, 
    age, height and ethnicity, providing functions for TLCO, DLCO, KCO and VA.

    It includes reference values for Caucasians aged 5-80 years.

    Hall GL, Filipow N, Ruppel G, Okitika T, Thompson B, Kirkby J, Steenbruggen I, Cooper BG, Stanojevic S; contributing 
    GLI Network members. Official ERS technical standard: Global Lung Function Initiative reference values for static lung 
    volumes in individuals of European ancestry. Eur Respir J. 2021 Mar 11;57(3):2000289. doi: 10.1183/13993003.00289-2020. 
    PMID: 33707167.
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
        """
        No height range given.
        """
        self.__lookup, self.__splines = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        """
        Loads and stores the coefficient and splines values.
        :return: both files as pandas dataframe
        """
        lookup_path = importlib.resources.open_binary('PySpiro.data', 'gli_2021_splines.csv')
        splines_path = importlib.resources.open_binary('PySpiro.data', 'gli_2021_coefficients.csv')
        lookup = pandas.read_csv(lookup_path, delimiter=";").set_index("age")
        splines = pandas.read_csv(splines_path, delimiter=";").set_index("var")
        self._age_range: tuple = (min(lookup.index), max(lookup.index))
        return lookup, splines

    def __get_splines(self, sex: int, age: float, parameter: int):
        """
        Yields the appropriated splines values based on the parameter, sex and age.
        :param sex: self.Sex enumration as integer value
        :param age: age as float
        :param parameter: self.Parameter enumeration as integer value
        """
        for i in ("Sspline", "Mspline", "Lspline"):
            yield self.__lookup["%s_%ss_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower(), i)].loc[age] # Change sth here

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """
        Calculate l, m and s values for the given parameters.
        """
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA
        sspline, mspline, lspline = self.__get_splines(sex, age, parameter) #LSpline not used.
        c = self.__splines["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]
        
        if self.Parameters(parameter).name in ['FRC', 'TLC', 'RV', 'RV_TLC']:
            s = numpy.exp(float(c.loc["p0"]) + (float(c.loc["p1"]) * numpy.log(age)) + sspline)
        elif self.Parameters(parameter).name in ['ERV', 'IC', 'VC']:
            s = numpy.exp(float(c.loc["p0"]) + (float(c.loc["p1"]) * numpy.log(age)))

        m = numpy.exp(float(c.loc["a0"]) + (float(c.loc["a1"]) * numpy.log(height)) + (float(c.loc["a2"]) * numpy.log(age)) + mspline)
        l = float(c.loc["q0"])

        return l, m, s

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float):
        """
        Returns % of predicted value.
        """
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else round(( value / m ) * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float):
        """
        Returns z-score value.
        """
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else (((value/m)**l) - 1) / (l * s)

    def lln(self, sex: int, age: float, height: float, parameter: int, value: float):
        """
        Returns lower limit of normal, by convention the lower 5th percentile.
        """
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if (l is pandas.NA or m is pandas.NA or s is pandas.NA) else numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))

    def all(self, sex: int, age: float, height: float, parameter: int, value: float):
        """
        Returns all values at once (percent, z-score and lln).
        """
        l, m, s = self.lms(sex, age, height, parameter, value)
        if (l is pandas.NA or m is pandas.NA or s is pandas.NA):
            return pandas.NA
        else:
            return round(( value / m ) * 100, 2), (((value/m)**l) - 1) / (l * s), numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))