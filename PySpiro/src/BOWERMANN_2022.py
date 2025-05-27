from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class BOWERMANN_2022(Reference):
    """
    Implementation of the race-neutral reference equations for FEV1, FVC and FEV1/FVC.
    
    Citation 1:
    Bowerman C, Bhakta NR, Brazzale D, Cooper BR, Cooper J, Gochicoa-Rangel L, Haynes J, Kaminsky DA, Lan LTT, 
    Masekela R, McCormack MC, Steenbruggen I, Stanojevic S. A Race-neutral Approach to the Interpretation of 
    Lung Function Measurements. Am J Respir Crit Care Med. 2023 Mar 15;207(6):768-774. 
    doi: 10.1164/rccm.202205-0963OC. PMID: 36383197.
    """

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3

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
        lookup_path = importlib.resources.open_binary('PySpiro.data', 'bowermann_2022_splines.csv')
        splines_path = importlib.resources.open_binary('PySpiro.data', 'bowermann_2022_coefficients.csv')
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
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age", "ignore")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA
        sspline, mspline, lspline = self.__get_splines(sex, age, parameter) #LSpline not used.
        c = self.__splines["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        if self.Parameters(parameter).name in ['FEV1', 'FVC']:
            l = c.loc["q0"]
        elif self.Parameters(parameter).name in ['FEV1FVC']:
            l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age))

        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + sspline)

        return l, m, s

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float, silent = True):
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