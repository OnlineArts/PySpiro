import numpy
import pandas as pd

from .src.spirometry.KUSTER_2008 import KUSTER_2008
from .src.spirometry.HANKINSON_1999 import HANKINSON_1999
from .src.spirometry.KUBOTA_2014 import KUBOTA_2014
from .src.spirometry.GLI_2012 import GLI_2012
from .src.spirometry.BOWERMANN_2022 import BOWERMANN_2022
from .src.diffusion.GLI_2017 import GLI_2017
from .src.diffusion.SCAPIS_2023 import SCAPIS_2023
from .src.volumes.GLI_2021 import GLI_2021
from .src.oscillometry.SCHULZ_2013 import SCHULZ_2013
from .src.classifiers.GOLD import GOLD
from .src.classifiers.STAR import STAR
from .src.classifiers.ATS_ERS_2022 import ATS_ERS_2022
from .src.viz import plot_centile_curves
from .src.comparison import compare_equations


class Spiro:
    """
    Interactive demo of the pyspiro package.

    Instantiating this class generates a realistic synthetic cohort, runs all
    available reference equations and severity classifiers, and prints the
    result.  It is intended as a quick smoke-test and usage showcase — not for
    production use.  Import individual equation classes directly instead:

        from pyspiro import GLI_2012, BOWERMANN_2022, compare_equations

    Conventions
    -----------
    sex        : 0 = female, 1 = male
    age        : years
    height     : cm
    ethnicity  : 1 = Caucasian, 2 = African-American, 3 = NE Asian, 4 = SE Asian
    """

    def __init__(self):
        self._df = self._make_cohort()

        self._apply_kuster_2008()
        self._apply_gli_2012()
        self._apply_schulz_2013()
        self._apply_gli_2017()
        self._apply_gli_2021()
        self._apply_bowermann_2022()
        self._apply_scapis_2023()
        self._apply_gold()
        self._apply_star()

        print("\n--- Cohort results ---")
        print(self._df.to_string())

        print("\n--- compare_equations() for patient 0 ---")
        print(self._cross_equation_example())

        print("\n--- plot_centile_curves() ---")
        print("Call plot_centile_curves(GLI_2012(), sex=1, height=175, "
              "ethnicity=1, parameter=GLI_2012.Parameters.FEV1) to generate "
              "a centile chart.  Requires matplotlib.")

    # ------------------------------------------------------------------
    # Synthetic cohort
    # ------------------------------------------------------------------

    @staticmethod
    def _make_cohort(n: int = 10, seed: int = 42) -> pd.DataFrame:
        """Return a physiologically consistent synthetic patient cohort."""
        rng = numpy.random.default_rng(seed)

        sex  = rng.choice([0, 1], size=n)
        male = sex == 1

        # Anthropometrics stratified by sex (German adult population)
        height = numpy.where(male,
            rng.normal(178.0, 7.0, n), rng.normal(165.0, 6.0, n)).round(1)
        weight = numpy.where(male,
            rng.normal(82.0, 12.0, n), rng.normal(68.0, 11.0, n)).round(1)
        age = rng.integers(18, 78, size=n).astype(float)

        # Spirometry: derive FEV1 from FVC × ratio to guarantee FEV1 ≤ FVC
        fvc = numpy.where(male,
            rng.normal(4.6, 0.75, n), rng.normal(3.4, 0.60, n)).round(2)
        ratio = numpy.clip(numpy.where(male,
            rng.normal(0.77, 0.07, n), rng.normal(0.80, 0.06, n)), 0.40, 0.95)
        fev1  = (fvc * ratio).round(2)
        fef75 = numpy.where(male,
            rng.normal(1.0, 0.35, n), rng.normal(0.8, 0.28, n)).clip(0.15).round(2)

        # Static lung volumes: VC slightly above FVC; TLC = VC + RV
        vc  = (fvc + rng.normal(0.1, 0.08, n)).clip(0.5).round(2)
        rv  = numpy.where(male,
            rng.normal(1.8, 0.35, n), rng.normal(1.5, 0.30, n)).clip(0.5).round(2)
        tlc = (vc + rv).round(2)

        # Diffusion: KCO in mmol/min/kPa/L (SI); females slightly higher
        kco = numpy.where(male,
            rng.normal(1.55, 0.22, n), rng.normal(1.70, 0.22, n)).clip(0.5).round(2)

        # Oscillometry: X10 reactance reported as absolute value
        x10 = numpy.abs(rng.normal(0.10, 0.05, n)).round(2)

        return pd.DataFrame({
            "age":       age,
            "sex":       sex,
            "height":    height,
            "weight":    weight,
            "ethnicity": rng.choice([1, 2, 3, 4], size=n),
            "FVC":       fvc,
            "FEV1":      fev1,
            "FEF75":     fef75,
            "VC":        vc,
            "RV":        rv,
            "TLC":       tlc,
            "KCO":       kco,
            "X10":       x10,
        })

    # ------------------------------------------------------------------
    # Reference equations
    # ------------------------------------------------------------------

    def _apply_kuster_2008(self):
        eq = KUSTER_2008()
        self._df["KUSTER_FEV1_pct"] = self._df.apply(
            lambda r: eq.percent(r.sex, r.age, r.height, 1, eq.Parameters.FEV1, r.FEV1), axis=1)
        self._df["KUSTER_FEV1_LLN"] = self._df.apply(
            lambda r: eq.lln(r.sex, r.age, r.height, 1, eq.Parameters.FEV1_LLN, r.FEV1), axis=1)

    def _apply_gli_2012(self):
        eq = GLI_2012()
        eq.set_strategy("closest")
        # Two separate compute() calls because FEV1 and FEF75 live in different columns.
        # ethnicity column used directly (values 1–4 from the synthetic cohort).
        self._df["GLI2012_FEV1_pct"] = eq.compute(
            self._df, eq.Parameters.FEV1,
            value_col='FEV1', ethnicity_col='ethnicity', metrics=('percent',))['percent']
        self._df["GLI2012_FEF75_pct"] = eq.compute(
            self._df, eq.Parameters.FEF75,
            value_col='FEF75', ethnicity_col='ethnicity', metrics=('percent',))['percent']

    def _apply_gli_2017(self):
        eq = GLI_2017()
        eq.set_strategy("closest")
        self._df["GLI2017_KCO_pct"] = eq.compute(
            self._df, eq.Parameters.KCO_SI,
            value_col='KCO', metrics=('percent',))['percent']

    def _apply_gli_2021(self):
        eq = GLI_2021()
        self._df["GLI2021_RV_pct"] = eq.compute(
            self._df, eq.Parameters.RV,
            value_col='RV', metrics=('percent',))['percent']

    def _apply_bowermann_2022(self):
        eq = BOWERMANN_2022()
        # Two compute() calls: different parameter → different measured-value column.
        self._df["BOWERMANN_FEV1_pct"] = eq.compute(
            self._df, eq.Parameters.FEV1,
            value_col='FEV1', metrics=('percent',))['percent']
        self._df["BOWERMANN_FVC_z"] = eq.compute(
            self._df, eq.Parameters.FVC,
            value_col='FVC', metrics=('zscore',))['zscore']

    def _apply_schulz_2013(self):
        # SCHULZ_2013 uses direct percentile regression, not LMS — no compute() API.
        eq = SCHULZ_2013()
        self._df[["X10_p05", "X10_p50", "X10_p95"]] = self._df.apply(
            lambda r: pd.Series(
                eq.percentiles(r.sex, r.age, r.height, r.weight, eq.Parameters.X10)
            ), axis=1)

    def _apply_scapis_2023(self):
        eq = SCAPIS_2023()
        eq.set_strategy("closest")
        self._df["SCAPIS_FEV1_LLN"] = eq.compute(
            self._df, eq.Parameters.pre_BD_FEV1,
            value_col='FEV1', metrics=('lln',))['lln']

    def _apply_gold(self):
        gold = GOLD()
        self._df["GOLD"] = self._df.apply(
            lambda r: gold.classify(FEV1p=r.GLI2012_FEV1_pct), axis=1)
        self._df["GOLD"] = pd.Categorical(
            self._df["GOLD"], categories=gold.get_order(), ordered=True)

    def _apply_star(self):
        star = STAR()
        self._df["STAR"] = self._df.apply(
            lambda r: star.classify(FEV1=r.FEV1, FVC=r.FVC), axis=1)

    def _cross_equation_example(self) -> pd.DataFrame:
        """Return a compare_equations() table for the first patient in the cohort."""
        patient = self._df.iloc[0]
        return compare_equations(
            patient,
            GLI_2012.Parameters.FEV1,
            equations=[GLI_2012(), BOWERMANN_2022()],
        )


if __name__ == '__main__':
    Spiro()
