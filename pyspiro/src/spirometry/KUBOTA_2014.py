from ..reference import Reference
from enum import Enum
import importlib.resources
import numpy
import pandas


class KUBOTA_2014(Reference):
    """
    JRS 2014 spirometry reference equations (Kubota et al. 2014).

    Japanese Respiratory Society reference equations for Japanese adults, derived
    using the LMS method. Covers males and females, age range 17-95 years.
    No ethnicity stratification (Japan-specific equations).

    LMS equation form (height in cm, age in years):
        L = q0 + q1*ln(Age) + Lspline   (Lspline non-zero for FEV1FVC only)
        M = exp(a0 + a1*ln(Ht) + a2*ln(Age) + Mspline)
        S = exp(p0 + p1*ln(Age) + Sspline)

    Age is floored to the nearest lower integer for spline lookup (consistent
    with the rspiro reference implementation).

    Citation:
        Kubota M, Kobayashi H, Quanjer PH, Omori H, Tatsumi K, Mishima M;
        Japanese Respiratory Society Committee for Pulmonary Physiology.
        Reference values for spirometry, including vital capacity, in Japanese
        adults calculated with the LMS method and compared with previous values.
        Respir Investig. 2014 Sep;52(5):242-50.
        doi: 10.1016/j.resinv.2014.03.003. PMID: 25278192.
    """

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        VC = 3
        FEV1FVC = 4

    _AGE_RANGE = (17, 95)

    def __init__(self):
        self.__lookup, self.__splines = self.__load_lookup_table()
        self._age_range = self._AGE_RANGE

    def __load_lookup_table(self):
        splines_path = importlib.resources.open_binary('pyspiro.data', 'kubota_2014_splines.csv')
        raw = pandas.read_csv(splines_path, index_col=0)

        # Pre-index by (parameter_name, gender) for O(1) age lookup
        lookup = {}
        for (f, gender), group in raw.groupby(['f', 'gender']):
            lookup[(f, int(gender))] = group.set_index('agebound')

        coeff_path = importlib.resources.open_binary('pyspiro.data', 'kubota_2014_coefficients.csv')
        coefficients = pandas.read_csv(coeff_path, delimiter=";").set_index("var")

        return lookup, coefficients

    def _gender(self, sex: int) -> int:
        """Map Sex enum value (0=female, 1=male) to CSV gender (1=male, 2=female)."""
        return 1 if sex == self.Sex.MALE.value else 2

    def __get_splines(self, sex: int, age_int: int, parameter: int):
        param_name = self.Parameters(parameter).name
        key = (param_name, self._gender(sex))

        if key not in self.__lookup:
            return numpy.nan, numpy.nan, numpy.nan

        table = self.__lookup[key]
        if age_int not in table.index:
            return numpy.nan, numpy.nan, numpy.nan

        row = table.loc[age_int]
        return float(row['Sspline']), float(row['Mspline']), row['Lspline']

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        age = self.validate_range(age, self._AGE_RANGE, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        age_int = int(age)  # floor, consistent with rspiro
        param_name = self.Parameters(parameter).name
        col = "%s_%ss" % (param_name, self.Sex(sex).name.lower())

        sspline, mspline, lspline = self.__get_splines(sex, age_int, parameter)
        if pandas.isna(mspline) or pandas.isna(sspline):
            return pandas.NA, pandas.NA, pandas.NA

        c = self.__splines[col]

        l = float(c.loc["q0"]) + float(c.loc["q1"]) * numpy.log(age)
        if not pandas.isna(lspline):
            l += float(lspline)

        m = numpy.exp(float(c.loc["a0"])
                      + float(c.loc["a1"]) * numpy.log(height)
                      + float(c.loc["a2"]) * numpy.log(age)
                      + mspline)
        s = numpy.exp(float(c.loc["p0"])
                      + float(c.loc["p1"]) * numpy.log(age)
                      + sspline)

        return l, m, s

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return % of predicted."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if m is pandas.NA else round(value / m * 100, 2)

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return z-score."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if l is pandas.NA else (((value / m) ** l) - 1) / (l * s)

    def lln(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return lower limit of normal (5th percentile)."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if l is pandas.NA else numpy.exp(numpy.log(1 - 1.645 * l * s) / l + numpy.log(m))

    def uln(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return upper limit of normal (95th percentile)."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        return pandas.NA if l is pandas.NA else numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m))

    def all(self, sex: int, age: float, height: float, parameter: int, value: float):
        """Return (percent, z-score, lln, uln) in a single call."""
        l, m, s = self.lms(sex, age, height, parameter, value)
        if l is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA, pandas.NA
        return (
            round(value / m * 100, 2),
            (((value / m) ** l) - 1) / (l * s),
            numpy.exp(numpy.log(1 - 1.645 * l * s) / l + numpy.log(m)),
            numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m)),
        )
