from ..reference import LMSReference
from enum import Enum
import importlib.resources
import numpy
import pandas


class JO_2018(LMSReference):
    """
    Korean KNHANES spirometry reference equations (Jo et al. 2018).

    Derived from the Korea National Health and Nutrition Examination Survey
    (KNHANES) IV (2007–2009) and V (2010–2012) using the LMS method.
    Covers Korean adults aged 19–90 years, both sexes. No ethnicity
    stratification (Korea-specific equations).

    LMS equation form (height in cm, age in years):
        L = q0 + q1*ln(Age) + Lspline   (Lspline non-zero for FEV1FVC females only)
        M = exp(a0 + a1*ln(Ht) + a2*ln(Age) + Mspline)
        S = exp(p0 + p1*ln(Age) + Sspline)

    Age is floored to the nearest lower integer for spline lookup.

    Spline tables are stored in jo_2018_splines.csv (extracted from
    Supplementary Tables 2–4 of the original publication).

    Citation:
        Jo BS, Myong JP, Rhee CK, Yoon HK, Koo JW, Kim HR. Reference Values
        for Spirometry Derived Using Lambda, Mu, Sigma (LMS) Method in Korean
        Adults: in Comparison with Previous References.
        J Korean Med Sci. 2018 Jan 15;33(3):e16.
        doi: 10.3346/jkms.2018.33.e16. PMID: 29215803.
    """

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3

    _AGE_RANGE = (19, 90)

    def __init__(self):
        self.__lookup, self.__coefficients = self.__load_data()
        self._age_range = self._AGE_RANGE

    def __load_data(self):
        splines_path = importlib.resources.open_binary('pyspiro.data', 'jo_2018_splines.csv')
        raw = pandas.read_csv(splines_path, index_col=0)

        lookup = {}
        for (f, gender), group in raw.groupby(['f', 'gender']):
            lookup[(f, int(gender))] = group.set_index('agebound')

        coeff_path = importlib.resources.open_binary('pyspiro.data', 'jo_2018_coefficients.csv')
        coefficients = pandas.read_csv(coeff_path, delimiter=';').set_index('var')

        return lookup, coefficients

    def _sex_to_gender(self, sex: int) -> int:
        return 1 if sex == self.Sex.MALE.value else 2

    def __get_splines(self, sex: int, age_int: int, parameter: int):
        param_name = self.Parameters(parameter).name
        key = (param_name, self._sex_to_gender(sex))

        if key not in self.__lookup:
            return pandas.NA, pandas.NA, pandas.NA

        table = self.__lookup[key]
        if age_int not in table.index:
            return pandas.NA, pandas.NA, pandas.NA

        row = table.loc[age_int]
        lspline = row['Lspline']
        lspline = float(lspline) if pandas.notna(lspline) else pandas.NA
        return float(row['Sspline']), float(row['Mspline']), lspline

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float = None) -> tuple:
        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        age_int = int(age)
        param_name = self.Parameters(parameter).name
        col = '%s_%ss' % (param_name, self.Sex(sex).name.lower())

        sspline, mspline, lspline = self.__get_splines(sex, age_int, parameter)
        if pandas.isna(mspline) or pandas.isna(sspline):
            return pandas.NA, pandas.NA, pandas.NA

        c = self.__coefficients[col]

        l = float(c.loc['q0']) + float(c.loc['q1']) * numpy.log(age)
        if not pandas.isna(lspline):
            l += float(lspline)

        m = numpy.exp(float(c.loc['a0'])
                      + float(c.loc['a1']) * numpy.log(height)
                      + float(c.loc['a2']) * numpy.log(age)
                      + mspline)
        s = numpy.exp(float(c.loc['p0'])
                      + float(c.loc['p1']) * numpy.log(age)
                      + sspline)

        return l, m, s
