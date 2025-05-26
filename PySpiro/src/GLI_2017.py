from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class GLI_2017(Reference):
    """
    This global lung function was published in 2017 by Stanojevic and includes as variable sex, age, height and ethnicity,
    providing functions for TLCO, DLCO, KCO and VA.

    It includes reference values for Caucasians aged 5-80 years.

    We here implement the corrected version of the reference values, which was published in 2020.

    Citation 1:
    Stanojevic S, Graham BL, Cooper BG, Thompson BR, Carter KW, Francis RW, Hall GL; Global Lung Function Initiative TLCO 
    working group; Global Lung Function Initiative (GLI) TLCO. Official ERS technical standards: Global Lung Function 
    Initiative reference values for the carbon monoxide transfer factor for Caucasians. Eur Respir J. 2017 
    Sep 11;50(3):1700010. doi: 10.1183/13993003.00010-2017. Erratum in: Eur Respir J. 2020 Oct 15;56(4):1750010. 
    doi: 10.1183/13993003.50010-2017. PMID: 28893868.

    Citation 2:
    "Official ERS technical standards: Global Lung Function Initiative reference values for the carbon monoxide transfer 
    factor for Caucasians." Sanja Stanojevic, Brian L. Graham, Brendan G. Cooper, Bruce R. Thompson, Kim W. Carter, Richard 
    W. Francis and Graham L. Hall on behalf of the Global Lung Function Initiative TLCO working group. Eur Respir J 2017; 
    50: 1700010. Eur Respir J. 2020 Oct 15;56(4):1750010. doi: 10.1183/13993003.50010-2017. Erratum for: Eur Respir J. 2017 
    Sep 11;50(3):1700010. doi: 10.1183/13993003.00010-2017. PMID: 33060163.
    """


    class Parameters(Enum):
        TLCO = 1 # SI Units
        DLCO = 2 # Traditional Units
        KCO_SI = 3 # SI Units
        KCO_trad = 4 # Traditional Units
        VA = 5

    def __init__(self):
        """
        No height range given.
        """
        self.__lookup, self.__splines = self.__load_lookup_table()
        self._age_range = (5, 80)


    def __load_lookup_table(self) -> tuple:
        """
        Loads and stores the coefficient and splines values.
        :return: both files as pandas dataframe
        """
        lookup_path = importlib.resources.open_binary('PySpiro.data', 'gli_2017_splines.csv')
        splines_path = importlib.resources.open_binary('PySpiro.data', 'gli_2017_coefficients.csv')
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
        print("%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower()))
        c = self.__splines["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        # AfrAm = int(ethnicity == self.Ethnicity["AFRICAN_AMERICAN"].value)
        # NEAsia = int(ethnicity == self.Ethnicity["NORTHEAST_ASIAN"].value)
        # SEAsia = int(ethnicity == self.Ethnicity["SOUTHEAST_ASIAN"].value)

        print(c.loc[["a0", "a1", "a2"]])
        print(type(c.loc["a1"]))

        l = c.loc["q0"]
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
