from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class SCAPIS_2023(Reference):
    """
    This set of lung function equations was published in 2023 by Malinovschi et al and includes pre- and post-bronchodialtion reference equations for FEV1, FVC, FEV1_FVC, DLCO 
    and KCO for a population aged 50 to 65 (SCAPIS: Swedish CArdioPulmonary bioImage Study). Note that this set was derived from a Swedish population only and may not be applicable 
    to other populations.

    Citation:
    Malinovschi A, Zhou X, Andersson A, Backman H, Bake B, Blomberg A, Caidahl K, Eriksson MJ, Eriksson Ström J, Hamrefors V, Hjelmgren O, Janson C, Karimi R, Kylhammar D, Lindberg A, 
    Lindberg E, Liv P, Olin AC, Shalabi A, Sköld CM, Sundström J, Tanash H, Torén K, Wollmer P, Zaigham S, Östgren CJ, Engvall JE. Consequences of Using Post- or Prebronchodilator 
    Reference Values in Interpreting Spirometry. Am J Respir Crit Care Med. 2023 Aug 15;208(4):461-471. doi: 10.1164/rccm.202212-2341OC. PMID: 37339507.
    """

    class Parameters(Enum):
        """
        All parameters.
        """
        pre_BD_FEV1 = 1
        post_BD_FEV1 = 2
        pre_BD_FVC = 3
        post_BD_FVC = 4
        pre_BD_FEV1_FVC = 5
        post_BD_FEV1_FVC = 6
        post_BD_DLCO = 7
        post_BD_KCO = 18

    def __init__(self):
        """
        Initiate the object.
        """
        self.__lookup, self.__splines = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        """
        Loads and stores the coefficient and splines values.
        :return: both files as pandas dataframe
        """
        lookup_path = importlib.resources.open_binary('pyspiro.data', 'scapis_2023_splines.csv')
        splines_path = importlib.resources.open_binary('pyspiro.data', 'scapis_2023_coefficients.csv')
        lookup = pandas.read_csv(lookup_path, delimiter=",", header = [0,1], index_col = 0)
        splines = pandas.read_csv(splines_path, delimiter=",", index_col=0)
        self._age_range: tuple = (min(lookup.index), max(lookup.index))
        return lookup, splines


    def __get_splines(self, sex: int, age: float, parameter: int):
        """
        Yields the appropriated splines values based on the parameter, sex and age.
        :param sex: self.Sex enumration as integer value
        :param age: age as float
        :param parameter: self.Parameter enumeration as integer value
        """
        for i in ("SSpline", "MSpline"):
            # No L-Splines
            yield self.__lookup.loc[age, ("%s_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower()), i)]

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """
        Calculate l, m and s values for the given parameters.
        """
        age = self.validate_range(round(age * 10) / 10, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline = self.__get_splines(sex, age, parameter)
        c = self.__splines["%s_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]
        
        m = numpy.exp(c.loc["M1"] + (c.loc["M2"] * numpy.log(height)) + (c.loc["M3"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["S1"] + (c.loc["S2"] * numpy.log(age)) + sspline)
        l = c.loc['L']
 
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
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA
        else:
            return round(( value / m ) * 100, 2), (((value/m)**l) - 1) / (l * s), numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))

