from ..reference import IntegerAgeLMSReference
from enum import Enum


class KUBOTA_2014(IntegerAgeLMSReference):
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
        doi: 10.1016/j.resinv.2014.03.003. PMID:  24998371.
    """

    _splines_csv = 'kubota_2014_splines.csv'
    _coeffs_csv = 'kubota_2014_coefficients.csv'

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        VC = 3
        FEV1FVC = 4

    _AGE_RANGE = (17, 95)
