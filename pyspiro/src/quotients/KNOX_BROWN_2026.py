import inspect
from enum import Enum

import pandas as pd

from .quotient import Quotient


class KNOX_BROWN_2026(Quotient):
    """
    Physiological quotients (Q) for spirometry, gas transfer and lung volumes.

    A physiological quotient expresses a measured value as a multiple of the 1st
    percentile ("minimally survivable") value observed in a hospital lung function
    population:

        Q = measured value / 1st percentile value

    The concept was introduced for FEV1 by MILLER and PEDERSEN (Eur Respir J 2010;
    35: 873-882) and extended by KNOX-BROWN et al. to FVC, FEV1/FVC, DLCO, KCO, VA
    and TLC using 7717 patients from Cambridge University Hospital (CUH) and 6054
    from Royal Papworth Hospital (RPH).

    Unlike a reference equation, a quotient needs no age, height or ethnicity: the
    1st percentile values were stable across age groups, and stable across sex for
    FEV1/FVC, DLCO and KCO.  This makes Q available for patients an equation cannot
    score at all.  The authors give this as a main motivation, citing the loss of
    602 (CUH) and 469 (RPH) patients from their TLC analyses for want of a predicted
    value.  In this package that limit is age 80 for GLI_2021 static lung volumes;
    GLI_2017 gas transfer runs to age 90 here, above the 85-year ceiling the authors
    report for their software.

    This is not a reference equation.  It is a Quotient, not a Reference: there is
    no predicted median, no z-score and no limit of normal to take.  Use it
    alongside an equation, not instead of one -- see expressions().

    Consensus 1st percentile values (table 2)
    -----------------------------------------
                                        Male    Female
        FEV1, L                         0.50    0.40
        FVC, L                          1.50    1.20
        FEV1/FVC, ratio                 0.15    0.15
        DLCO, mmol/min/kPa              1.60    1.60
        KCO, mmol/min/kPa/L             0.40    0.40
        VA, L                           2.40    2.00
        TLC, L                          2.60    2.30

    Units
    -----
    DLCO and KCO 1st percentiles were published in SI units only.  The DLCO_trad and
    KCO_trad parameters are derived here by applying the standard 2.9863 conversion
    (1 mmol/min/kPa = 2.9863 mL/min/mmHg); those two thresholds are NOT published
    values.  DLCO_SI corresponds to GLI_2017.Parameters.TLCO and DLCO_trad to
    GLI_2017.Parameters.DLCO -- note that GLI_2017 uses the TLCO/DLCO naming for the
    SI/traditional split, whereas this paper writes DLCO throughout and reports SI.

    FEV1/FVC is passed as a fraction (0-1), consistent with the LMS equations in
    this package.  A ratio given on the 0-100 scale is rejected rather than silently
    rescaled, because a genuine quotient can legitimately exceed 1.

    Interpretation
    --------------
    Higher Q is better; Q=1 means the measurement sits at the minimally survivable
    value.  In adjusted Cox models (table 4) every quotient except FEV1/FVCQ was
    associated with all-cause mortality, VAQ most strongly (HR 0.31-0.32 per 1-unit
    increment).  FEV1/FVCQ was not (HR 0.99-1.01, p>0.4); the authors conclude that
    expressing FEV1/FVC as a quotient "offers little benefit clinically".  Published
    hazard ratios and Harrell's C-indexes are available via hazard_ratio(), and the
    cohort distributions of each quotient via cohort_reference().

    Caveats
    -------
    The derivation cohorts were 95% (CUH) and 97% (RPH) White European, and 1st
    percentiles could not be derived separately for patients under 30 years or at
    extremes of height (<130 or >190 cm).  The authors state that until the values
    are replicated in more diverse cohorts and against outcomes other than mortality,
    "physiological quotients cannot replace reference equation-based metrics".
    NON_WHITE_PERCENTILE_1 holds the CUH non-White 1st percentiles from table 2 for
    sensitivity checking; they are not an alternative set of thresholds to apply.
    The authors report those values as similar to the consensus for all measures,
    which holds for six of the seven: the exception is KCO in females, 0.79
    (95% CI 0.59-1.00) against a consensus of 0.40, where the consensus value falls
    below the confidence interval.  Read KCOQ in non-White women with that in mind.

    Citation:
        Knox-Brown B, Robertson L, Amaral AFS, Sylvester KP. Physiological quotients
        and mortality: redefining lung function interpretation beyond FEV1.
        Eur Respir J 2026; 68: 2502204.
        DOI: 10.1183/13993003.02204-2025

    Prior work:
        Miller MR, Pedersen OF. New concepts for expressing forced expiratory volume
        in 1 s arising from survival analysis. Eur Respir J 2010; 35: 873-882.
        DOI: 10.1183/09031936.00110809
    """

    # 1 mmol/min/kPa = 2.9863 mL/min/mmHg
    SI_TO_TRADITIONAL = 2.9863

    # Highest quotient band used in the published Kaplan-Meier analyses (figures 3 and 4)
    MAX_BAND = 6

    class Parameters(Enum):
        FEV1 = 1
        FVC = 2
        FEV1FVC = 3
        DLCO_SI = 4     # SI units (mmol/min/kPa)          -> GLI_2017.Parameters.TLCO
        DLCO_trad = 5   # Traditional units (mL/min/mmHg)  -> GLI_2017.Parameters.DLCO
        KCO_SI = 6      # SI units (mmol/min/kPa/L)
        KCO_trad = 7    # Traditional units (mL/min/mmHg/L)
        VA = 8
        TLC = 9

    # Table 2 consensus 1st percentiles, sex-specific: (female, male)
    _PERCENTILE_1_BY_SEX = {
        Parameters.FEV1.value: (0.40, 0.50),
        Parameters.FVC.value:  (1.20, 1.50),
        Parameters.VA.value:   (2.00, 2.40),
        Parameters.TLC.value:  (2.30, 2.60),
    }

    # Table 2 consensus 1st percentiles that were stable across both age and sex.
    # The two *_trad entries are unit conversions, not published values.
    _PERCENTILE_1_SEX_NEUTRAL = {
        Parameters.FEV1FVC.value:   0.15,
        Parameters.DLCO_SI.value:   1.60,
        Parameters.DLCO_trad.value: 1.60 * SI_TO_TRADITIONAL,
        Parameters.KCO_SI.value:    0.40,
        Parameters.KCO_trad.value:  0.40 * SI_TO_TRADITIONAL,
    }

    # FEV1/FVC is a fraction (0-1), consistent with the LMS equations in this package
    _FRACTION_PARAMETERS = frozenset({Parameters.FEV1FVC.value})

    # Traditional-unit variants share the survival statistics of their SI counterpart
    _UNIT_ALIASES = {
        Parameters.DLCO_trad.value: Parameters.DLCO_SI.value,
        Parameters.KCO_trad.value:  Parameters.KCO_SI.value,
    }

    # Table 2: 1st percentile (95% CI) for non-White individuals at CUH.
    # Reported for comparison with the consensus values only; RPH data were excluded
    # by the authors for insufficient sample size (n=178 male, n=249 female).
    NON_WHITE_PERCENTILE_1 = {
        Parameters.FEV1.value:     {"male": (0.52, (0.43, 0.73)), "female": (0.47, (0.37, 0.98))},
        Parameters.FVC.value:      {"male": (1.47, (1.35, 2.02)), "female": (1.25, (1.12, 1.48))},
        Parameters.FEV1FVC.value:  {"male": (0.14, (0.13, 0.18)), "female": (0.14, (0.10, 0.15))},
        Parameters.DLCO_SI.value:  {"male": (1.94, (1.52, 2.90)), "female": (2.13, (1.59, 2.86))},
        Parameters.KCO_SI.value:   {"male": (0.47, (0.37, 0.77)), "female": (0.79, (0.59, 1.00))},
        Parameters.VA.value:       {"male": (2.33, (0.92, 2.67)), "female": (1.91, (1.77, 2.19))},
        Parameters.TLC.value:      {"male": (2.73, (2.59, 3.53)), "female": (2.33, (2.25, 2.65))},
    }

    # Hazard ratios for all-cause mortality per 1-unit increase in the quotient.
    #   'unadjusted' : supplementary table S3, which also reports Harrell's C-index
    #   'model1'     : table 4, adjusted for age, sex, height, smoking, referral reason
    #   'model2'     : table 4, model 1 plus ethnicity (White/non-White) as main effect
    #                  and interaction term
    HAZARD_RATIOS = {
        "CUH": {
            Parameters.FEV1.value: {
                "unadjusted": {"hr": 0.75, "ci": (0.73, 0.77), "p": "<0.001",
                               "c_index": 0.66, "c_index_ci": (0.65, 0.67)},
                "model1": {"hr": 0.77, "ci": (0.74, 0.80), "p": "<0.001"},
                "model2": {"hr": 0.77, "ci": (0.74, 0.80), "p": "<0.001"},
            },
            Parameters.FVC.value: {
                "unadjusted": {"hr": 0.43, "ci": (0.40, 0.47), "p": "<0.001",
                               "c_index": 0.65, "c_index_ci": (0.64, 0.66)},
                "model1": {"hr": 0.46, "ci": (0.42, 0.51), "p": "<0.001"},
                "model2": {"hr": 0.45, "ci": (0.41, 0.49), "p": "<0.001"},
            },
            Parameters.FEV1FVC.value: {
                "unadjusted": {"hr": 0.90, "ci": (0.88, 0.93), "p": "<0.001",
                               "c_index": 0.55, "c_index_ci": (0.54, 0.56)},
                "model1": {"hr": 0.99, "ci": (0.95, 1.02), "p": "0.462"},
                "model2": {"hr": 0.99, "ci": (0.95, 1.03), "p": "0.545"},
            },
            Parameters.DLCO_SI.value: {
                "unadjusted": {"hr": 0.56, "ci": (0.54, 0.59), "p": "<0.001",
                               "c_index": 0.72, "c_index_ci": (0.71, 0.73)},
                "model1": {"hr": 0.52, "ci": (0.50, 0.56), "p": "<0.001"},
                "model2": {"hr": 0.53, "ci": (0.50, 0.56), "p": "<0.001"},
            },
            Parameters.KCO_SI.value: {
                "unadjusted": {"hr": 0.45, "ci": (0.43, 0.48), "p": "<0.001",
                               "c_index": 0.70, "c_index_ci": (0.69, 0.71)},
                "model1": {"hr": 0.52, "ci": (0.48, 0.57), "p": "<0.001"},
                "model2": {"hr": 0.53, "ci": (0.49, 0.57), "p": "<0.001"},
            },
            Parameters.VA.value: {
                "unadjusted": {"hr": 0.34, "ci": (0.30, 0.38), "p": "<0.001",
                               "c_index": 0.63, "c_index_ci": (0.62, 0.64)},
                "model1": {"hr": 0.32, "ci": (0.29, 0.38), "p": "<0.001"},
                "model2": {"hr": 0.31, "ci": (0.27, 0.36), "p": "<0.001"},
            },
            Parameters.TLC.value: {
                "unadjusted": {"hr": 0.77, "ci": (0.69, 0.85), "p": "<0.001",
                               "c_index": 0.54, "c_index_ci": (0.53, 0.55)},
                "model1": {"hr": 0.61, "ci": (0.54, 0.69), "p": "<0.001"},
                "model2": {"hr": 0.59, "ci": (0.52, 0.67), "p": "<0.001"},
            },
        },
        "RPH": {
            Parameters.FEV1.value: {
                "unadjusted": {"hr": 0.73, "ci": (0.71, 0.74), "p": "<0.001",
                               "c_index": 0.66, "c_index_ci": (0.65, 0.67)},
                "model1": {"hr": 0.78, "ci": (0.75, 0.80), "p": "<0.001"},
                "model2": {"hr": 0.78, "ci": (0.75, 0.80), "p": "<0.001"},
            },
            Parameters.FVC.value: {
                "unadjusted": {"hr": 0.41, "ci": (0.39, 0.44), "p": "<0.001",
                               "c_index": 0.66, "c_index_ci": (0.65, 0.67)},
                "model1": {"hr": 0.43, "ci": (0.39, 0.46), "p": "<0.001"},
                "model2": {"hr": 0.43, "ci": (0.39, 0.46), "p": "<0.001"},
            },
            Parameters.FEV1FVC.value: {
                "unadjusted": {"hr": 0.88, "ci": (0.84, 0.91), "p": "<0.001",
                               "c_index": 0.51, "c_index_ci": (0.50, 0.52)},
                "model1": {"hr": 1.01, "ci": (0.97, 1.05), "p": "0.622"},
                "model2": {"hr": 1.01, "ci": (0.97, 1.05), "p": "0.705"},
            },
            Parameters.DLCO_SI.value: {
                "unadjusted": {"hr": 0.51, "ci": (0.49, 0.53), "p": "<0.001",
                               "c_index": 0.73, "c_index_ci": (0.72, 0.73)},
                "model1": {"hr": 0.51, "ci": (0.49, 0.53), "p": "<0.001"},
                "model2": {"hr": 0.51, "ci": (0.49, 0.53), "p": "<0.001"},
            },
            Parameters.KCO_SI.value: {
                "unadjusted": {"hr": 0.45, "ci": (0.43, 0.47), "p": "<0.001",
                               "c_index": 0.70, "c_index_ci": (0.69, 0.71)},
                "model1": {"hr": 0.55, "ci": (0.52, 0.58), "p": "<0.001"},
                "model2": {"hr": 0.54, "ci": (0.51, 0.57), "p": "<0.001"},
            },
            Parameters.VA.value: {
                # Supplementary table S3 prints the unadjusted CI as (0.30, 0.35), i.e.
                # with the upper bound equal to the point estimate; transcribed as published.
                "unadjusted": {"hr": 0.35, "ci": (0.30, 0.35), "p": "<0.001",
                               "c_index": 0.65, "c_index_ci": (0.65, 0.66)},
                "model1": {"hr": 0.31, "ci": (0.28, 0.34), "p": "<0.001"},
                "model2": {"hr": 0.31, "ci": (0.28, 0.34), "p": "<0.001"},
            },
            Parameters.TLC.value: {
                "unadjusted": {"hr": 0.56, "ci": (0.53, 0.61), "p": "<0.001",
                               "c_index": 0.59, "c_index_ci": (0.58, 0.60)},
                "model1": {"hr": 0.52, "ci": (0.48, 0.57), "p": "<0.001"},
                "model2": {"hr": 0.53, "ci": (0.48, 0.57), "p": "<0.001"},
            },
        },
    }

    # Observed quotient distributions in the two derivation cohorts (supplementary
    # tables S1 and S2).  mean (SD) for every quotient except FEV1/FVCQ, which is
    # reported as median (IQR).  Use these to place a patient's quotient in the
    # context of the population it was derived from -- they are not normal ranges.
    # Referral-reason strata are published but not transcribed here.
    COHORT_REFERENCE = {
        "CUH": {
            "overall":   {"n": 7717, Parameters.FEV1.value: (5.54, 2.07), Parameters.FVC.value: (2.68, 0.70),
                          Parameters.FEV1FVC.value: (4.32, (1.86, 5.03)), Parameters.DLCO_SI.value: (4.15, 1.51),
                          Parameters.KCO_SI.value: (3.28, 0.89), Parameters.VA.value: (2.30, 0.47),
                          Parameters.TLC.value: (2.44, 0.52)},
            "male":      {"n": 3780, Parameters.FEV1.value: (5.65, 2.21), Parameters.FVC.value: (2.84, 0.72),
                          Parameters.FEV1FVC.value: (4.11, (1.80, 4.92)), Parameters.DLCO_SI.value: (4.67, 1.69),
                          Parameters.KCO_SI.value: (3.19, 0.93), Parameters.VA.value: (2.42, 0.49),
                          Parameters.TLC.value: (2.66, 0.53)},
            # TLCQ SD for CUH females is printed as 5.85 in supplementary table S1, which is
            # implausible next to the male SD of 0.53; recorded as None rather than propagated.
            "female":    {"n": 3937, Parameters.FEV1.value: (5.43, 1.93), Parameters.FVC.value: (2.52, 0.64),
                          Parameters.FEV1FVC.value: (4.50, (1.92, 5.13)), Parameters.DLCO_SI.value: (3.65, 1.10),
                          Parameters.KCO_SI.value: (3.36, 0.83), Parameters.VA.value: (2.17, 0.41),
                          Parameters.TLC.value: (2.22, None)},
            "age_lt_40": {"n": 1043, Parameters.FEV1.value: (7.66, 1.78), Parameters.FVC.value: (3.18, 0.69),
                          Parameters.FEV1FVC.value: (5.03, (2.23, 5.54)), Parameters.DLCO_SI.value: (5.29, 1.41),
                          Parameters.KCO_SI.value: (4.01, 0.68), Parameters.VA.value: (2.43, 0.47),
                          Parameters.TLC.value: (2.40, 0.47)},
            "age_40_49": {"n": 951,  Parameters.FEV1.value: (6.58, 1.84), Parameters.FVC.value: (3.00, 0.68),
                          Parameters.FEV1FVC.value: (4.68, (2.21, 5.19)), Parameters.DLCO_SI.value: (4.89, 1.48),
                          Parameters.KCO_SI.value: (3.66, 0.76), Parameters.VA.value: (2.44, 0.47),
                          Parameters.TLC.value: (2.48, 0.51)},
            "age_50_59": {"n": 1623, Parameters.FEV1.value: (5.83, 1.83), Parameters.FVC.value: (2.80, 0.64),
                          Parameters.FEV1FVC.value: (4.44, (1.87, 5.04)), Parameters.DLCO_SI.value: (4.48, 1.39),
                          Parameters.KCO_SI.value: (3.44, 0.81), Parameters.VA.value: (2.38, 0.46),
                          Parameters.TLC.value: (2.47, 0.52)},
            "age_60_69": {"n": 2189, Parameters.FEV1.value: (4.97, 1.82), Parameters.FVC.value: (2.56, 0.62),
                          Parameters.FEV1FVC.value: (4.10, (1.73, 4.89)), Parameters.DLCO_SI.value: (3.84, 1.33),
                          Parameters.KCO_SI.value: (3.05, 0.82), Parameters.VA.value: (2.28, 0.46),
                          Parameters.TLC.value: (2.49, 0.53)},
            "age_ge_70": {"n": 1911, Parameters.FEV1.value: (4.27, 1.51), Parameters.FVC.value: (2.28, 0.57),
                          Parameters.FEV1FVC.value: (3.86, (1.71, 4.70)), Parameters.DLCO_SI.value: (3.21, 1.12),
                          Parameters.KCO_SI.value: (2.79, 0.79), Parameters.VA.value: (2.09, 0.42),
                          Parameters.TLC.value: (2.34, 0.56)},
        },
        "RPH": {
            # VAQ SD for the RPH overall row is printed as 0.91 in supplementary table S2,
            # out of keeping with the male (0.54) and female (0.45) strata; recorded as None.
            "overall":   {"n": 6054, Parameters.FEV1.value: (4.79, 1.84), Parameters.FVC.value: (2.31, 0.71),
                          Parameters.FEV1FVC.value: (4.81, (4.11, 5.32)), Parameters.DLCO_SI.value: (3.40, 1.44),
                          Parameters.KCO_SI.value: (2.96, 0.91), Parameters.VA.value: (2.05, None),
                          Parameters.TLC.value: (2.27, 0.59)},
            "male":      {"n": 3345, Parameters.FEV1.value: (4.92, 1.91), Parameters.FVC.value: (2.42, 0.73),
                          Parameters.FEV1FVC.value: (4.74, (4.00, 5.28)), Parameters.DLCO_SI.value: (3.73, 1.60),
                          Parameters.KCO_SI.value: (2.88, 0.93), Parameters.VA.value: (2.13, 0.54),
                          Parameters.TLC.value: (2.41, 0.62)},
            "female":    {"n": 2709, Parameters.FEV1.value: (4.64, 1.75), Parameters.FVC.value: (2.18, 0.65),
                          Parameters.FEV1FVC.value: (4.89, (4.25, 5.36)), Parameters.DLCO_SI.value: (3.01, 1.10),
                          Parameters.KCO_SI.value: (3.06, 0.87), Parameters.VA.value: (1.96, 0.45),
                          Parameters.TLC.value: (2.10, 0.49)},
            "age_lt_40": {"n": 528,  Parameters.FEV1.value: (6.51, 2.37), Parameters.FVC.value: (2.81, 0.86),
                          Parameters.FEV1FVC.value: (5.38, (4.78, 5.67)), Parameters.DLCO_SI.value: (4.68, 1.55),
                          Parameters.KCO_SI.value: (3.87, 0.78), Parameters.VA.value: (2.20, 0.58),
                          Parameters.TLC.value: (2.30, 0.54)},
            "age_40_49": {"n": 524,  Parameters.FEV1.value: (5.72, 2.07), Parameters.FVC.value: (2.64, 0.78),
                          Parameters.FEV1FVC.value: (5.07, (4.58, 5.43)), Parameters.DLCO_SI.value: (4.21, 1.58),
                          Parameters.KCO_SI.value: (3.48, 0.92), Parameters.VA.value: (2.19, 0.54),
                          Parameters.TLC.value: (2.33, 0.61)},
            "age_50_59": {"n": 1099, Parameters.FEV1.value: (5.11, 1.83), Parameters.FVC.value: (2.43, 0.69),
                          Parameters.FEV1FVC.value: (4.91, (4.28, 5.36)), Parameters.DLCO_SI.value: (3.76, 1.45),
                          Parameters.KCO_SI.value: (3.19, 0.92), Parameters.VA.value: (2.12, 0.51),
                          Parameters.TLC.value: (2.30, 0.60)},
            "age_60_69": {"n": 1571, Parameters.FEV1.value: (4.58, 1.69), Parameters.FVC.value: (2.30, 0.67),
                          Parameters.FEV1FVC.value: (4.67, (3.93, 5.21)), Parameters.DLCO_SI.value: (3.31, 1.33),
                          Parameters.KCO_SI.value: (2.84, 0.84), Parameters.VA.value: (2.08, 0.51),
                          Parameters.TLC.value: (2.34, 0.62)},
            "age_ge_70": {"n": 2332, Parameters.FEV1.value: (4.19, 1.33), Parameters.FVC.value: (2.07, 0.57),
                          Parameters.FEV1FVC.value: (4.66, (3.99, 5.24)), Parameters.DLCO_SI.value: (2.83, 1.08),
                          Parameters.KCO_SI.value: (2.61, 0.74), Parameters.VA.value: (1.95, 0.45),
                          Parameters.TLC.value: (2.19, 0.56)},
        },
    }

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    #
    # percentile1(), quotient() and band() are inherited from Quotient; the tables
    # above are all this paper adds to them.  In this class:
    #
    #   percentile1()  needs sex for FEV1, FVC, VA and TLC, and ignores it for
    #                  FEV1/FVC, DLCO and KCO, whose 1st percentiles were stable
    #                  across sex as well as age.
    #   band()         is the whole-quotient grouping of the Kaplan-Meier analyses
    #                  (figures 3 and 4), 0 to MAX_BAND.  The paper attaches no
    #                  severity labels to these bands and neither does this class.
    #                  For orientation, in the COPD cohort a FEV1Q, DLCOQ or VAQ of
    #                  2 corresponded to roughly 70% 5-year survival; in the ILD
    #                  cohort an FVCQ of 2 to roughly 60% and a DLCOQ of 2 to
    #                  roughly 50%.

    # ------------------------------------------------------------------
    # Batch API
    # ------------------------------------------------------------------

    def compute(self, df: pd.DataFrame, parameter, value_col: str,
                sex_col: str = 'sex',
                metrics: tuple = ('quotient',)) -> pd.DataFrame:
        """
        Apply the quotient to every row of a DataFrame.

        Parameters
        ----------
        df        : DataFrame with one patient per row.
        parameter : Parameters member (or its integer value) to evaluate.
        value_col : column name holding the measured value.
        sex_col   : column name for sex (0=female, 1=male).  Default 'sex'.
                    Only read for the sex-specific parameters; pass None to omit it
                    for FEV1/FVC, DLCO and KCO.
        metrics   : any subset of ('quotient', 'percentile1', 'band').
                    Default: ('quotient',).

        Returns
        -------
        DataFrame indexed like df with one column per requested metric.

        Examples
        --------
        >>> kbq = KNOX_BROWN_2026()
        >>> df['FEV1Q'] = kbq.compute(df, KNOX_BROWN_2026.Parameters.FEV1,
        ...                           value_col='FEV1')['quotient']
        >>> # DLCO needs no sex column
        >>> kbq.compute(df, KNOX_BROWN_2026.Parameters.DLCO_SI,
        ...             value_col='DLCO', sex_col=None, metrics=('quotient', 'band'))
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            raise ValueError("KNOX_BROWN_2026.compute: unknown parameter %r." % (parameter,))

        unknown = set(metrics) - {'quotient', 'percentile1', 'band'}
        if unknown:
            raise ValueError(
                "KNOX_BROWN_2026.compute: unknown metric(s) %s; "
                "expected any of ('quotient', 'percentile1', 'band')." % sorted(unknown)
            )

        needs_sex = param in self._PERCENTILE_1_BY_SEX
        if needs_sex and sex_col is None:
            raise ValueError(
                "KNOX_BROWN_2026.compute: %s has sex-specific 1st percentiles; "
                "pass sex_col='<column_name>'." % self.Parameters(param).name
            )
        if value_col is None and metrics != ('percentile1',):
            raise ValueError(
                "KNOX_BROWN_2026.compute: metrics 'quotient' and 'band' require a "
                "measured value; pass value_col='<column_name>'."
            )

        def _sex(row):
            return row[sex_col] if needs_sex else None

        dispatch = {
            'quotient':    lambda r: self.quotient(param, r[value_col], _sex(r)),
            'percentile1': lambda r: self.percentile1(param, _sex(r)),
            'band':        lambda r: self.band(param, r[value_col], _sex(r)),
        }

        result = {m: df.apply(dispatch[m], axis=1) for m in metrics}
        return pd.DataFrame(result, index=df.index)

    # ------------------------------------------------------------------
    # Published statistics
    # ------------------------------------------------------------------

    def hazard_ratio(self, parameter, site: str = "CUH", model: str = "model1") -> dict:
        """
        Return the published hazard ratio for all-cause mortality per 1-unit increase.

        Parameters
        ----------
        parameter : Parameters member (or its integer value).  The traditional-unit
                    variants resolve to their SI counterpart, since the survival
                    analyses were performed in SI units.
        site      : 'CUH' (n=7717, 19% mortality over 5.8 years) or
                    'RPH' (n=6054, 39% mortality over 5.5 years).
        model     : 'unadjusted' (supplementary table S3, includes Harrell's C-index),
                    'model1' or 'model2' (table 4).

        Returns
        -------
        dict with 'hr', 'ci', 'p' and -- for 'unadjusted' -- 'c_index' and
        'c_index_ci'.  Returns an empty dict on invalid input.
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            return {}
        param = self._UNIT_ALIASES.get(param, param)

        if site not in self.HAZARD_RATIOS:
            self._warn("site must be 'CUH' or 'RPH', got %r." % (site,))
            return {}
        entry = self.HAZARD_RATIOS[site][param]
        if model not in entry:
            self._warn("model must be 'unadjusted', 'model1' or 'model2', got %r." % (model,))
            return {}
        return dict(entry[model])

    def cohort_reference(self, parameter, site: str = "CUH", stratum: str = "overall") -> dict:
        """
        Return the quotient's distribution in a derivation cohort stratum.

        Parameters
        ----------
        parameter : Parameters member (or its integer value); traditional-unit
                    variants resolve to their SI counterpart.
        site      : 'CUH' or 'RPH'.
        stratum   : 'overall', 'male', 'female', 'age_lt_40', 'age_40_49',
                    'age_50_59', 'age_60_69' or 'age_ge_70'.

        Returns
        -------
        dict with 'n' and either {'mean', 'sd'} or, for FEV1/FVC, {'median', 'iqr'}.
        'sd' is None where the published value appears to be a typographical error.
        Returns an empty dict on invalid input.

        These are observed distributions in a referred hospital population, not
        normal ranges; every quotient declined significantly with age.
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            return {}
        param = self._UNIT_ALIASES.get(param, param)

        if site not in self.COHORT_REFERENCE:
            self._warn("site must be 'CUH' or 'RPH', got %r." % (site,))
            return {}
        if stratum not in self.COHORT_REFERENCE[site]:
            self._warn("unknown stratum %r; expected one of %s."
                       % (stratum, sorted(self.COHORT_REFERENCE[site])))
            return {}

        row = self.COHORT_REFERENCE[site][stratum]
        centre, spread = row[param]
        if param == self.Parameters.FEV1FVC.value:
            return {"n": row["n"], "median": centre, "iqr": spread}
        return {"n": row["n"], "mean": centre, "sd": spread}

    # ------------------------------------------------------------------
    # Side-by-side interpretation
    # ------------------------------------------------------------------

    def expressions(self, parameter, value: float, sex: int = None,
                    equation=None, equation_parameter=None,
                    age: float = None, height: float = None, ethnicity: int = None) -> dict:
        """
        Express one measurement as a quotient and, optionally, as % predicted and z-score.

        This reproduces the comparison the paper makes: the same measured value read
        three ways.  Where the reference equation cannot score the patient -- an
        82-year-old for TLC via GLI_2021, say -- 'percent' and 'zscore' come back as
        pd.NA while the quotient is still defined.

        Parameters
        ----------
        parameter          : KNOX_BROWN_2026.Parameters member.
        value              : the measured value.
        sex                : 0 = female, 1 = male.
        equation           : optional Reference instance (e.g. GLI_2017(), GLI_2021(),
                             BOWERMAN_2022()) to take % predicted and z-score from.
        equation_parameter : that equation's own Parameters member for the same
                             measurement.  Required when equation is given, because
                             the enums are not harmonised across classes.
        age, height        : required when equation is given (years, cm).
        ethnicity          : required when the equation's lms() takes an ethnicity
                             argument (GLI_2012, HANKINSON_1999, KUSTER_2008);
                             not passed otherwise.

        Returns
        -------
        dict with 'parameter', 'value', 'percentile_1', 'quotient', 'band' and, when
        an equation is supplied, 'equation', 'percent' and 'zscore'.

        No unit conversion is performed: pass a value in the units both the quotient
        parameter and the equation parameter expect.

        Examples
        --------
        >>> from pyspiro import GLI_2017, KNOX_BROWN_2026
        >>> kbq = KNOX_BROWN_2026()
        >>> kbq.expressions(KNOX_BROWN_2026.Parameters.DLCO_SI, value=3.2, sex=1,
        ...                 equation=GLI_2017(), equation_parameter=GLI_2017.Parameters.TLCO,
        ...                 age=64, height=178)
        """
        param = self._resolve_parameter(parameter)
        if param is pd.NA:
            return {}

        out = {
            "parameter": self.Parameters(param).name,
            "value": value,
            "percentile_1": self.percentile1(param, sex),
            "quotient": self.quotient(param, value, sex),
            "band": self.band(param, value, sex),
        }
        if equation is None:
            return out

        if equation_parameter is None:
            raise ValueError(
                "KNOX_BROWN_2026.expressions: equation_parameter is required when an "
                "equation is supplied; the Parameters enums are not shared across classes."
            )
        if age is None or height is None:
            raise ValueError(
                "KNOX_BROWN_2026.expressions: age and height are required when an "
                "equation is supplied."
            )

        out["equation"] = type(equation).__name__

        kwargs = {
            "sex": int(sex),
            "age": float(age),
            "height": float(height),
            "parameter": equation_parameter,
            "value": float(value),
        }
        source = getattr(equation, "lms", equation.percent)
        if "ethnicity" in inspect.signature(source).parameters:
            if ethnicity is None:
                # Some equations (e.g. KUSTER_2008) accept the argument and ignore it,
                # so this asks rather than guessing a code the equation may reject.
                raise ValueError(
                    "KNOX_BROWN_2026.expressions: %s takes an ethnicity argument; "
                    "pass ethnicity=." % type(equation).__name__
                )
            kwargs["ethnicity"] = int(ethnicity)

        out["percent"] = equation.percent(**kwargs)
        out["zscore"] = equation.zscore(**kwargs)
        return out
