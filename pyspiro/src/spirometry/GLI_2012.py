from ..reference import SplineReference
from enum import Enum
import numpy
import pandas


class GLI_2012(SplineReference):
    """
    GLI 2012 multi-ethnic spirometry reference equations (Quanjer et al. 2012).

    Global Lung Function Initiative reference equations for spirometry covering
    four ethnic groups plus a composite "other/mixed" group, both sexes, and an
    age range of 3-95 years (FEF25-75 and FEF75: 3-90 years).

    Variables: sex (0=female, 1=male), age (years), height (cm), ethnicity.
    Parameters: FEV1, FVC, FEV1/FVC, FEF25-75, FEF75, FEV0.75, FEV0.75/FVC.
    Ethnicity: Caucasian (1), African-American (2), NE Asian (3), SE Asian (4),
    Other/mixed (5). Any other code raises ValueError.

    Lspline, Mspline and Sspline are linearly interpolated between the
    quarter-year rows of the look-up tables, as prescribed by the online
    supplement (section 4); the closed-form terms use the exact age
    (see SplineReference._age_and_splines).

    FEV0.75 and FEV0.75/FVC are given by the source as equations without
    look-up tables, for Caucasians aged 3-7 years only; other ethnicities
    and ages return NA.

    Citation:
        Quanjer PH, Stanojevic S, Cole TJ, et al.; ERS Global Lung Function
        Initiative. Multi-ethnic reference values for spirometry for the 3-95-yr
        age range: the global lung function 2012 equations. Eur Respir J.
        2012;40(6):1324-43. doi: 10.1183/09031936.00080312. PMID: 22743675.
    """

    _splines_csv = 'gli_2012_splines.csv'
    _coeffs_csv  = 'gli_2012_coefficients.csv'

    _EQUATION_ONLY_AGE_RANGE = (3, 7)

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3
        FEF25_75 = 4
        FEF75 = 5
        FEV075 = 6
        FEV075FVC = 7

    class Ethnicity(Enum):
        CAUCASIAN = 1
        AFRICAN_AMERICAN = 2
        NORTHEAST_ASIAN = 3
        SOUTHEAST_ASIAN = 4
        OTHER = 5

    _EQUATION_ONLY = (Parameters.FEV075, Parameters.FEV075FVC)

    def _check_ethnicity(self, ethnicity):
        if ethnicity not in [e.value for e in self.Ethnicity]:
            raise ValueError(
                "GLI_2012: unknown ethnicity code %r; expected 1 (Caucasian), 2 (African-American), "
                "3 (NE Asian), 4 (SE Asian) or 5 (Other/mixed)." % (ethnicity,))

    def _equation_only_lms(self, age: float, height: float, ethnicity: int, parameter, c) -> tuple:
        """FEV0.75 and FEV0.75/FVC: equations without look-up tables, Caucasians aged 3-7 y only."""
        if ethnicity != self.Ethnicity["CAUCASIAN"].value:
            if not self._silent:
                print("GLI_2012: %s is only defined for Caucasians (ethnicity 1)" % parameter.name)
            return pandas.NA, pandas.NA, pandas.NA
        age = self.validate_range(age, self._EQUATION_ONLY_AGE_RANGE, "age")
        if age is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA
        return self._equation_only_equation(c, parameter, age, height)

    def _equation_only_equation(self, c, parameter, age, height) -> tuple:
        # FEV0.75 uses age itself, FEV0.75/FVC uses ln(age) (look-up workbook, "NOTE: Age, not log(Age)")
        age_term = age if parameter == self.Parameters.FEV075 else numpy.log(age)
        l = c.loc["q0"]
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * age_term))
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * age_term))
        return l, m, s

    _ARRAY_LMS = True

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        self._check_ethnicity(ethnicity)
        parameter = self.Parameters(parameter)

        if parameter in self._EQUATION_ONLY:
            c = self._coefficients[self._spline_prefix(sex, parameter)]
            return self._equation_only_lms(age, height, ethnicity, parameter, c)

        return self._spline_lms(sex, age, height, ethnicity, parameter)

    def _lms_equation(self, c, parameter, age, height, ethnicity, sspline, mspline, lspline) -> tuple:
        # Group indicators; (ethnicity == code) * 1 works for a scalar code and for an array of codes
        AfrAm = (ethnicity == self.Ethnicity["AFRICAN_AMERICAN"].value) * 1
        NEAsia = (ethnicity == self.Ethnicity["NORTHEAST_ASIAN"].value) * 1
        SEAsia = (ethnicity == self.Ethnicity["SOUTHEAST_ASIAN"].value) * 1
        Other = (ethnicity == self.Ethnicity["OTHER"].value) * 1

        l = c.loc["q0"] + (c.loc["q1"] * numpy.log(age)) + lspline
        m = numpy.exp(c.loc["a0"] + (c.loc["a1"] * numpy.log(height)) + (c.loc["a2"] * numpy.log(age)) + (c.loc["a3"] * AfrAm) + (c.loc["a4"] * NEAsia) + (c.loc["a5"] * SEAsia) + (c.loc["a6"] * Other) + mspline)
        s = numpy.exp(c.loc["p0"] + (c.loc["p1"] * numpy.log(age)) + (c.loc["p2"] * AfrAm) + (c.loc["p3"] * NEAsia) + (c.loc["p4"] * SEAsia) + (c.loc["p5"] * Other) + sspline)

        return l, m, s

    def _lms_arrays(self, sex, age, height, ethnicity, parameter) -> tuple:
        for code in numpy.unique(ethnicity):
            self._check_ethnicity(int(code))
        return super()._lms_arrays(sex, age, height, ethnicity, self.Parameters(parameter))

    def _sex_lms_arrays(self, sex: int, age, height, ethnicity, parameter) -> tuple:
        if parameter not in self._EQUATION_ONLY:
            return super()._sex_lms_arrays(sex, age, height, ethnicity, parameter)

        c = self._coefficients[self._spline_prefix(sex, parameter)]
        caucasian = ethnicity == self.Ethnicity["CAUCASIAN"].value
        if not self._silent:
            for _ in range(int((~caucasian).sum())):
                print("GLI_2012: %s is only defined for Caucasians (ethnicity 1)" % parameter.name)
        age = numpy.array(age, dtype=float)
        age[caucasian], out_of_range = self._validate_range_array(age[caucasian], self._EQUATION_ONLY_AGE_RANGE, "age")
        na = ~caucasian
        na[caucasian] = out_of_range
        age[na] = self._EQUATION_ONLY_AGE_RANGE[0]      # placeholder, masked later
        with numpy.errstate(all="ignore"):
            l, m, s = self._equation_only_equation(c, parameter, age, height)
        return l, m, s, na
