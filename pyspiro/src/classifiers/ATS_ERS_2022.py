import pandas as pd

from ..reference import Classifier


class ATS_ERS_2022(Classifier):
    """
    ATS/ERS 2022 spirometry interpretation pattern classifier.

    Classifies spirometry results into standard ventilatory patterns using
    z-scores, following the 2022 ERS/ATS technical standard on interpretive
    strategies for routine lung function tests (Stanojevic et al. 2022).

    All inputs are z-scores. The lower limit of normal (LLN) corresponds to
    z = -1.645 (5th percentile of the reference population).

    Required keyword arguments for classify():
        FEV1_z    — FEV1 z-score
        FVC_z     — FVC z-score
        FEV1FVC_z — FEV1/FVC z-score

    Optional keyword argument:
        TLC_z     — TLC z-score; when provided, enables distinction between
                    true restriction and non-specific pattern, and confirms
                    the mixed obstructive-restrictive pattern.

    Decision tree (Stanojevic et al. 2022, Eur Respir J, Figure 1):
    FEV1/FVC_z < −1.645?
    ├─ YES → Obstruction
    │         FVC_z < −1.645?
    │           ├─ YES + TLC_z < −1.645  → Mixed obstructive-restrictive
    │           ├─ YES + TLC_z ≥ −1.645  → Obstructive (air trapping, not restriction)
    │           ├─ YES + TLC unknown     → Obstructive with reduced FVC
    │           └─ NO                   → Obstructive
    └─ NO  → No obstruction
              FVC_z < −1.645?
                ├─ YES + TLC_z < −1.645  → Restrictive
                ├─ YES + TLC_z ≥ −1.645  → Non-specific (NSIP)
                ├─ YES + TLC unknown     → Possible restriction
                └─ NO → FEV1_z < −1.645? → Non-specific (NSIP)
                                       NO → Normal

    Patterns returned by classify():

        "Normal"
            FEV1/FVC ≥ LLN, FVC ≥ LLN, FEV1 ≥ LLN.

        "Obstructive"
            FEV1/FVC < LLN.
            If FVC is also < LLN but TLC ≥ LLN (or TLC confirms no restriction),
            the FVC reduction is attributed to air trapping rather than restriction,
            and the pattern remains obstructive.

        "Obstructive with reduced FVC"
            FEV1/FVC < LLN, FVC < LLN, TLC not measured.
            Spirometry alone cannot distinguish air trapping from a superimposed
            restrictive defect; TLC measurement is recommended.

        "Mixed obstructive-restrictive"
            FEV1/FVC < LLN, FVC < LLN, TLC < LLN.
            Both obstructive and restrictive defects confirmed.

        "Possible restriction"
            FEV1/FVC ≥ LLN, FVC < LLN, TLC not measured.
            Reduced FVC with preserved ratio; TLC measurement required to
            distinguish true restriction from non-specific pattern.

        "Restrictive"
            FEV1/FVC ≥ LLN, FVC < LLN, TLC < LLN.
            True restrictive defect confirmed.

        "Non-specific (NSIP)"
            FEV1/FVC ≥ LLN, FVC < LLN, TLC ≥ LLN.
            Both FEV1 and FVC are proportionally reduced but TLC is preserved;
            pattern does not fit obstruction or restriction.
            Also returned when FEV1/FVC ≥ LLN, FVC ≥ LLN, but FEV1 < LLN
            (unusual discordant pattern).

    Citation:
        Stanojevic S, Kaminsky DA, Miller MR, et al. ERS/ATS technical standard
        on interpretive strategies for routine lung function tests. Eur Respir J.
        2022;60(1):2101499. doi: 10.1183/13993003.01499-2021. PMID: 35169025.
    """

    # z-score corresponding to the 5th percentile (LLN / ULN boundary)
    _LLN_Z: float = -1.645

    # Pattern label constants — use these for comparisons rather than bare strings
    NORMAL                      = "Normal"
    OBSTRUCTIVE                 = "Obstructive"
    OBSTRUCTIVE_REDUCED_FVC     = "Obstructive with reduced FVC"
    MIXED                       = "Mixed obstructive-restrictive"
    POSSIBLE_RESTRICTION        = "Possible restriction"
    RESTRICTIVE                 = "Restrictive"
    NSIP                        = "Non-specific (NSIP)"

    # Logical ordering for use with pd.Categorical
    _order = [
        NORMAL,
        OBSTRUCTIVE,
        OBSTRUCTIVE_REDUCED_FVC,
        MIXED,
        POSSIBLE_RESTRICTION,
        RESTRICTIVE,
        NSIP,
    ]

    def classify(self, **kwargs) -> str:
        """
        Classify the spirometry pattern from z-scores.

        Required kwargs: FEV1_z, FVC_z, FEV1FVC_z.
        Optional kwargs: TLC_z (float or None).
        Returns a pattern string (see class docstring) or pd.NA on invalid input.
        """
        # ── Parse required inputs ───────────────────────────────────────────
        try:
            fev1_z    = float(kwargs["FEV1_z"])
            fvc_z     = float(kwargs["FVC_z"])
            fev1fvc_z = float(kwargs["FEV1FVC_z"])
        except KeyError as e:
            print(f"ATS_ERS_2022: missing required argument {e}. "
                  "FEV1_z, FVC_z and FEV1FVC_z are all required.")
            return pd.NA
        except (TypeError, ValueError):
            print("ATS_ERS_2022: FEV1_z, FVC_z and FEV1FVC_z must be numeric.")
            return pd.NA

        # ── Parse optional TLC ──────────────────────────────────────────────
        tlc_z = kwargs.get("TLC_z", None)
        if tlc_z is not None:
            try:
                tlc_z = float(tlc_z)
                if pd.isna(tlc_z):
                    tlc_z = None
            except (TypeError, ValueError):
                tlc_z = None

        z = self._LLN_Z

        # ── Decision tree (Stanojevic et al. 2022, Fig. 1) ─────────────────

        if fev1fvc_z < z:
            # ── Obstruction present ─────────────────────────────────────────
            if fvc_z < z:
                # FVC also reduced — air trapping vs mixed defect
                if tlc_z is None:
                    # Cannot distinguish without TLC
                    return self.OBSTRUCTIVE_REDUCED_FVC
                elif tlc_z < z:
                    # TLC confirms restriction component
                    return self.MIXED
                else:
                    # TLC ≥ LLN → FVC reduction due to air trapping, not restriction
                    return self.OBSTRUCTIVE
            else:
                return self.OBSTRUCTIVE

        else:
            # ── No obstruction (FEV1/FVC ≥ LLN) ────────────────────────────
            if fvc_z < z:
                # Reduced FVC with preserved ratio
                if tlc_z is None:
                    return self.POSSIBLE_RESTRICTION
                elif tlc_z < z:
                    return self.RESTRICTIVE
                else:
                    # TLC ≥ LLN despite low FVC → non-specific pattern
                    return self.NSIP
            else:
                # FVC ≥ LLN
                if fev1_z >= z:
                    return self.NORMAL
                else:
                    # FEV1 < LLN with normal FVC and ratio — discordant pattern.
                    # Arises when FEV1/FVC is close to LLN and FVC is near its
                    # upper range, or from inter-equation inconsistency.
                    return self.NSIP
