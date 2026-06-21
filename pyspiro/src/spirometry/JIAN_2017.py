from ..reference import LMSReference
from enum import Enum
import importlib.resources
import math
import numpy
import pandas


class JIAN_2017(LMSReference):
    """
    Chinese spirometry reference equations (Jian et al. 2017).

    LMS (Lambda-Mu-Sigma) equations for FVC, FEV1, FEV1/FVC, PEF, and MMEF in
    Han Chinese aged 4–80 years, both sexes. Derived from 7,115 healthy
    non-smokers recruited across 24 centers nationwide (January 2007 – December
    2010).

    Equation form (height h in cm, age in years):
        M = exp(m0 + m_h × ln(h) + m_age × ln(age) + Mspline)
        S = exp(s0 + s_h × ln(h) + s_age × ln(age) + Sspline)
        L = l0 + l_age × ln(age) + Lspline

    Spline tables are sampled at 0.2-year steps (4.0 – 81.0); input age is
    floored to the nearest 0.2 year for lookup.

    Note: FEV1FVC is expressed as a percentage (0–100), not a unitless ratio.
    Pass the measured FEV1/FVC as a percentage (e.g. 83.0) when computing
    percent(), zscore(), lln(), or uln() for this parameter.

    Spline tables are stored in jian_2017_splines.csv (extracted from
    Supplementary Tables S1–S2 of the original publication).
    Regression coefficients are in jian_2017_coefficients.csv (Table S3).

    Citation:
        Jian W, Gao Y, Hao C, Wang N, Ai T, Liu C, Xu Y, Kang J, Yang L,
        Shen H, Guan W, Jiang M, Zhong N, Zheng J. Reference values for
        spirometry in Chinese aged 4–80 years. J Thorac Dis.
        2017;9(11):4538-4549. doi: 10.21037/jtd.2017.10.110. PMID: 29268393.
    """

    class Parameters(Enum):
        FVC     = 1
        FEV1    = 2
        FEV1FVC = 3
        PEF     = 4
        MMEF    = 5

    _AGE_RANGE = (4, 80)

    def __init__(self):
        self._lookup, self._coefficients = self._load_data()
        self._age_range = self._AGE_RANGE

    def _load_data(self):
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'jian_2017_splines.csv').open('rb') as f:
            lookup = pandas.read_csv(f, delimiter=';', index_col=0)
        lookup.index = lookup.index.round(1)

        with (pkg / 'jian_2017_coefficients.csv').open('rb') as f:
            coefficients = pandas.read_csv(f, delimiter=';').set_index('var')

        return lookup, coefficients

    def _floor_age(self, age: float) -> float:
        """Floor age to the nearest 0.2-year step used in the spline tables."""
        return round(math.floor(age * 5) / 5, 1)

    def _sex_label(self, sex: int) -> str:
        return 'males' if sex == self.Sex.MALE.value else 'females'

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float = None) -> tuple:
        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA

        age_key = self._floor_age(float(age))
        param_name = self.Parameters(parameter).name
        sex_label = self._sex_label(sex)
        col = f'{param_name}_{sex_label}'
        prefix = f'{param_name}_{sex_label}'

        c = self._coefficients[col]
        row = self._lookup.loc[age_key]

        mspline = float(row[f'{prefix}_Mspline'])
        sspline = float(row[f'{prefix}_Sspline'])
        lspline = float(row[f'{prefix}_Lspline'])

        l = float(c['l0']) + float(c['l_age']) * numpy.log(age) + lspline
        m = numpy.exp(
            float(c['m0'])
            + float(c['m_h'])   * numpy.log(height)
            + float(c['m_age']) * numpy.log(age)
            + mspline
        )
        s = numpy.exp(
            float(c['s0'])
            + float(c['s_h'])   * numpy.log(height)
            + float(c['s_age']) * numpy.log(age)
            + sspline
        )

        return l, m, s
