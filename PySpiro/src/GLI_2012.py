from PySpiro.src.reference import Reference
from enum import Enum
import pandas
import numpy


class GLI_2012(Reference):
    """
    This global lung function was published in 2012 by Quanjer and includes as variable sex, age, height and ethnicity,
    providing functions for FEV1, FVC and FEV1/FVC.

    Citation:
    Quanjer PH, Stanojevic S, Cole TJ, Baur X, Hall GL, Culver BH, Enright PL, Hankinson JL, Ip MS, Zheng J, Stocks J;
    ERS Global Lung Function Initiative. Multi-ethnic reference values for spirometry for the 3-95-yr age range: the
    global lung function 2012 equations. Eur Respir J. 2012 Dec;40(6):1324-43. doi: 10.1183/09031936.00080312
    """

    class Parameters(Enum):
        """
        All lung spirometry parameter.
        """
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3

    class Ethnicity(Enum):
        """
        All accepted ethnicities.
        """
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2
        NORTHEAST_ASIAN = 3
        SOUTHEAST_ASIAN = 4

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
        lookup = pandas.read_csv("data/gli_2012_splines.csv", delimiter=";").set_index("age")
        splines = pandas.read_csv("data/gli_2012_coefficients.csv", delimiter=";").set_index("var")
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
            yield self.__lookup["%s_%ss_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower(), i)].loc[age]

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        age = self.validate_age(round(age * 4) / 4)
        sspline, mspline, lspline = self.__get_splines(sex, age, parameter)
        c = self.__splines["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        AfrAm = int(ethnicity == self.Ethnicity["AFRICAN_AMERICAN"].value)
        NEAsia = int(ethnicity == self.Ethnicity["NORTHEAST_ASIAN"].value)
        SEAsia = int(ethnicity == self.Ethnicity["SOUTHEAST_ASIAN"].value)

        l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age)) + lspline
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + (c.loc["a3"] * AfrAm) + (c.loc["a4"] * NEAsia) + (c.loc["a5"] * SEAsia) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + (c.loc["p2"] * AfrAm) + (c.loc["p3"] * NEAsia) + (c.loc["p4"] * SEAsia) + sspline)

        return l, m, s

    def predict(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return round(( value / m ) * 100, 2)

    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return (((value/m)**l) - 1) / (l * s)

    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))

    def all(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        l, m, s = self.lms(sex, age, height, ethnicity, parameter, value)
        return round(( value / m ) * 100, 2), (((value/m)**l) - 1) / (l * s), numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))