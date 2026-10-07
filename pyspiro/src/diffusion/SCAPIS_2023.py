from ..reference import LMSReference
from enum import Enum
import importlib.resources
import numpy
import pandas


class SCAPIS_2023(LMSReference):
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
        post_BD_KCO = 8

    def __init__(self):
        self.__lookup, self.__coefficients = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'scapis_2023_splines.csv').open('rb') as f:
            lookup = pandas.read_csv(f, delimiter=",", header=[0, 1], index_col=0)
        with (pkg / 'scapis_2023_coefficients.csv').open('rb') as f:
            coefficients = pandas.read_csv(f, delimiter=",", index_col=0)
        self._age_range: tuple = (min(lookup.index), max(lookup.index))
        return lookup, coefficients

    def __get_splines(self, sex: int, age: float, parameter: int):
        for i in ("SSpline", "MSpline"):
            yield self.__lookup.loc[age, ("%s_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower()), i)]

    @staticmethod
    def _equation(c, age, height, sspline, mspline) -> tuple:
        """The (L, M, S) equation; accepts scalars and NumPy arrays alike."""
        m = numpy.exp(c.loc["M1"] + (c.loc["M2"] * numpy.log(height)) + (c.loc["M3"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["S1"] + (c.loc["S2"] * numpy.log(age)) + sspline)
        l = c.loc['L']
        return l, m, s

    _ARRAY_LMS = True

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(round(age * 10) / 10, self._age_range, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        sspline, mspline = self.__get_splines(sex, age, parameter)
        c = self.__coefficients["%s_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]
        return self._equation(c, age, height, sspline, mspline)

    def _sex_lms_arrays(self, sex: int, age, height, ethnicity, parameter) -> tuple:
        if numpy.isnan(age).any():
            raise ValueError("cannot convert float NaN to integer")    # as round(age * 10) in lms()
        column = "%s_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())
        # numpy.round rounds half to even, as round() does
        age, na = self._validate_range_array(numpy.round(age * 10) / 10, self._age_range, "age")
        age = numpy.where(na, self._age_range[0], age)
        positions = self.__lookup.index.get_indexer(age)
        if (positions < 0).any():
            raise KeyError("SCAPIS_2023: age not in the spline table")    # as .loc in lms()
        sspline, mspline = (self.__lookup[(column, name)].to_numpy(dtype=float)[positions]
                            for name in ("SSpline", "MSpline"))
        with numpy.errstate(all="ignore"):
            l, m, s = self._equation(self.__coefficients[column], age, height, sspline, mspline)
        return l, m, s, na
