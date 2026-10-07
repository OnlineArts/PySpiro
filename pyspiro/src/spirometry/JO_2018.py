from ..reference import IntegerAgeLMSReference
from enum import Enum


class JO_2018(IntegerAgeLMSReference):
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

    _splines_csv = 'jo_2018_splines.csv'
    _coeffs_csv = 'jo_2018_coefficients.csv'

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3

    _AGE_RANGE = (19, 90)
