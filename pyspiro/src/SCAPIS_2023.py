from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class SCAPIS_2023(Reference):
    """
    SCAPIS 2023 pre- and post-bronchodilator reference equations (Malinovschi et al. 2023).

    Reference equations derived from the Swedish CArdioPulmonary bioImage Study
    (SCAPIS), covering spirometry and diffusion capacity for adults aged 50-65
    years. Provides both pre- and post-bronchodilator reference values.
    Note: derived from a Swedish population; applicability to other populations
    may be limited.

    Variables: sex (0=female, 1=male), age (years, 50-65), height (cm).
    Parameters: pre/post-BD FEV1, FVC, FEV1/FVC; post-BD DLCO, KCO.
    No ethnicity stratification.

    Citation:
        Malinovschi A, Zhou X, Andersson A, et al. Consequences of Using Post-
        or Prebronchodilator Reference Values in Interpreting Spirometry.
        Am J Respir Crit Care Med. 2023;208(4):461-471.
        doi: 10.1164/rccm.202212-2341OC. PMID: 37339507.
    """

    class Parameters(Enum):
        pre_BD_FEV1 = 1
        post_BD_FEV1 = 2
        pre_BD_FVC = 3
        post_BD_FVC = 4
        pre_BD_FEV1_FVC = 5
        post_BD_FEV1_FVC = 6
        post_BD_DLCO = 7
        post_BD_KCO = 18

    def __init__(self):
        self.__lookup, self.__splines = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        lookup_path = importlib.resources.open_binary('pyspiro.data', 'scapis_2023_splines.csv')
        splines_path = importlib.resources.open_binary('pyspiro.data', 'scapis_2023_coefficients.csv')
        lookup = pandas.read_csv(lookup_path, delimiter=",", header = [0,1], index_col = 0)
        splines = pandas.read_csv(splines_path, delimiter=",", index_col=0)
        self._age_range: tuple = (min(lookup.index), max(lookup.index))
        return lookup, splines


    def __get_splines(self, sex: int, age: float, parameter: int):
        for i in ("SSpline", "MSpline"):
            yield self.__lookup.loc[age, ("%s_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower()), i)]

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
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
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA
        else:
            return round(( value / m ) * 100, 2), (((value/m)**l) - 1) / (l * s), numpy.exp(numpy.log(1 - 1.645 * l * s)/ l + numpy.log(m))

