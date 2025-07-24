from .reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class SCHULZ_2013(Reference):
    """
    A dataset for impulse oscillometry reference equations published by Schulz et al. 2013.

    citation:
    Schulz H, Flexeder C, Behr J, Heier M, Holle R, Huber RM, Jörres RA, Nowak D, Peters A, 
    Wichmann HE, Heinrich J, Karrasch S; KORA Study Group. Reference values of impulse oscillometric 
    lung function indices in adults of advanced age. PLoS One. 2013 May 15;8(5):e63366. 
    doi: 10.1371/journal.pone.0063366. PMID: 23691036; PMCID: PMC3655177.
    """


    class Parameters(Enum):
        R10 = 1
        R15 = 2
        R25 = 3
        R35 = 4
        X10 = 5
        X20 = 6
        X25 = 7
        X35 = 8

    def __init__(self):
        """
        No height range given.
        """
        self.__lookup = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        """
        Loads and stores the coefficient and splines values.
        :return: both files as pandas dataframe
        """
        splines_path = importlib.resources.open_binary('pyspiro.data', 'schulz_2013_splines.csv')
        splines = pandas.read_csv(splines_path, delimiter=";").set_index("Var")
        return splines

    def __get_splines(self, sex: int, pct: float, parameter: int):
        """
        Yields the appropriated splines values based on the parameter, sex and age.
        :param sex: self.Sex enumration as integer value
        :param pct: percentile as float, can be 0.05, 0.5 or 0.95
        :param parameter: self.Parameter enumeration as integer value
        """

        for i in ("intercept", "age", "height", "weight"):
            yield self.__lookup["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())].loc["%s_%s" % (i, pct)]

    def percentiles(self, sex: int, age: float, height: float, weight: float, parameter: int) -> tuple:
        """
        Return the 5, 50 and 95 percentile values.
        """
        if age is pandas.NA or sex is pandas.NA or height is pandas.NA or weight is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        q1, q2, q3, q4 = self.__get_splines(sex, pct = 0.05, parameter = parameter)
        q4 = 0 if pandas.isna(q4) else q4
        p5 = q1 + (q2 * age) + (q3 * height) + (q4 *weight)

        q1, q2, q3, q4 = self.__get_splines(sex, parameter = parameter, pct = 0.50)
        q4 = 0 if pandas.isna(q4) else q4
        p50 = q1 + (q2 * age) + (q3 * height) + (q4 *weight)

        q1, q2, q3, q4 = self.__get_splines(sex, parameter = parameter, pct = 0.95)
        q4 = 0 if pandas.isna(q4) else q4
        p95 = q1 + (q2 * age) + (q3 * height) + (q4 *weight)

        return p5, p50, p95

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """
        Not implemented.
        """
        pass

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float):
        """
        Not implemented.        
        """
        pass

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float):
        """
        Not implemented.
        """
        pass

    def lln(self, sex: int, age: float, height: float, weight: float, parameter: int, value: float):
        """
        Returns lower limit of normal, by convention the lower 5th percentile.
        """
        p5, p50, p95 = self.percentiles(sex, age, height, weight, parameter, value)
        return pandas.NA if (p5 is pandas.NA or p50 is pandas.NA or p95 is pandas.NA) else p5

    def all(self, sex: int, age: float, height: float, weight: float, parameter: int, value: float):
        """
        Returns all values at once (5th, 50th and 95th percentile).
        """
        p5, p50, p95 = self.percentiles(sex, age, height, weight, parameter, value)
        if (p5 is pandas.NA or p50 is pandas.NA or p95 is pandas.NA):
            return pandas.NA, pandas.NA, pandas.NA
        else:
            return p5, p50, p95