from ..reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class GLI_2017(Reference):
    """
    GLI 2017 lung diffusion capacity reference equations (Stanojevic et al. 2017).

    Global Lung Function Initiative reference equations for the carbon monoxide
    transfer factor in Caucasians. Covers both sexes, age range 5-80 years.
    This implementation uses the corrected 2020 erratum values.

    Variables: sex (0=female, 1=male), age (years), height (cm).
    Parameters: TLCO (SI), DLCO (traditional), KCO (SI), KCO (traditional), VA.
    No ethnicity stratification (Caucasian population only).

    Citation:
        Stanojevic S, Graham BL, Cooper BG, et al.; GLI TLCO working group.
        Official ERS technical standards: Global Lung Function Initiative
        reference values for the carbon monoxide transfer factor for Caucasians.
        Eur Respir J. 2017;50(3):1700010. doi: 10.1183/13993003.00010-2017.
        Erratum: Eur Respir J. 2020;56(4):1750010.
        doi: 10.1183/13993003.50010-2017. PMID: 28893868.
    """

    class Parameters(Enum):
        TLCO = 1       # SI units (mmol/min/kPa)
        DLCO = 2       # Traditional units (mL/min/mmHg)
        KCO_SI = 3     # SI units (mmol/min/kPa/L)
        KCO_trad = 4   # Traditional units (mL/min/mmHg/L)
        VA = 5

    def __init__(self):
        self.__lookup, self.__splines = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        lookup_path = importlib.resources.open_binary('pyspiro.data', 'gli_2017_splines.csv')
        splines_path = importlib.resources.open_binary('pyspiro.data', 'gli_2017_coefficients.csv')
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

        l = c.loc["q0"]
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + sspline)

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