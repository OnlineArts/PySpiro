"""Executable checks for the usage examples in README.md.

Each test mirrors a code block from the README so that documentation and the
public API cannot drift apart unnoticed. The synthetic ``df`` built in
``setUp`` supplies every column the README snippets reference (lower/upper-case
measured-value columns, ``eth``, ``weight``, etc.).
"""

import unittest

import numpy as np
import pandas as pd

from pyspiro import (
    GLI_2012,
    BOWERMAN_2022,
    KUSTER_2008,
    HANKINSON_1999,
    SCHULZ_2013,
    CALOGERO_2013,
    RAMSEY_2024,
    WODEHOUSE_2003,
    PCD_SEVERITY,
    GOLD,
    compare_equations,
    plot_centile_curves,
)


def _cohort(n: int = 8, seed: int = 0) -> pd.DataFrame:
    """A small synthetic cohort exposing every column the README uses."""
    rng = np.random.default_rng(seed)
    sex = rng.choice([0, 1], size=n)
    male = sex == 1
    height = np.where(male, rng.normal(178, 6, n), rng.normal(165, 6, n)).round(1)
    weight = np.where(male, rng.normal(82, 10, n), rng.normal(68, 9, n)).round(1)
    age = rng.integers(20, 75, size=n).astype(float)
    fvc = np.where(male, rng.normal(4.6, 0.6, n), rng.normal(3.4, 0.5, n)).round(2)
    ratio = np.clip(rng.normal(0.78, 0.05, n), 0.45, 0.92)
    fev1 = (fvc * ratio).round(2)
    return pd.DataFrame(
        {
            "sex": sex,
            "age": age,
            "height": height,
            "weight": weight,
            "eth": rng.choice([1, 2, 3], size=n),
            # column aliases used by the various README snippets
            "fev1": fev1,
            "fvc": fvc,
            "FEV1": fev1,
            "FVC": fvc,
            "rrs6": rng.normal(7.0, 1.5, n).round(2),
            "lci": rng.normal(7.5, 1.2, n).round(2),
        }
    )


class TestReadmeLMSExamples(unittest.TestCase):
    """README: 'LMS-based equations (GLI_2012, BOWERMAN_2022, ...)'."""

    def setUp(self):
        self.df = _cohort()

    def test_gli_and_bowerman_compute(self):
        df = self.df.copy()
        gli = GLI_2012()
        results = gli.compute(
            df,
            GLI_2012.Parameters.FEV1,
            value_col="fev1",
            ethnicity_col="eth",
        )
        df[["fev1_pct", "fev1_z", "fev1_lln", "fev1_uln"]] = results

        bow = BOWERMAN_2022()
        df[["fvc_pct", "fvc_z", "fvc_lln", "fvc_uln"]] = bow.compute(
            df, BOWERMAN_2022.Parameters.FVC, value_col="fvc"
        )

        self.assertEqual(len(results), len(df))
        for col in ("fev1_pct", "fev1_z", "fev1_lln", "fev1_uln",
                    "fvc_pct", "fvc_z", "fvc_lln", "fvc_uln"):
            self.assertIn(col, df.columns)

    def test_gli_compute_with_overridden_column_names(self):
        df = self.df.rename(
            columns={"sex": "gender", "age": "age_years", "height": "ht_cm"}
        )
        gli = GLI_2012()
        results = gli.compute(
            df,
            GLI_2012.Parameters.FEV1,
            sex_col="gender",
            age_col="age_years",
            height_col="ht_cm",
            value_col="fev1",
            ethnicity_col="eth",
            metrics=("percent", "lln"),
        )
        self.assertIn("percent", results.columns)
        self.assertIn("lln", results.columns)


class TestReadmePolynomialExamples(unittest.TestCase):
    """README: 'Polynomial equations (KUSTER_2008, HANKINSON_1999)'."""

    def setUp(self):
        self.df = _cohort()

    def test_kuster_percent_and_lln(self):
        df = self.df.copy()
        kus = KUSTER_2008()
        df["fev1_pct"] = kus.compute(
            df, KUSTER_2008.Parameters.FEV1,
            value_col="fev1", metrics=("percent",))["percent"]
        df["fev1_lln"] = kus.compute(
            df, KUSTER_2008.Parameters.FEV1_LLN,
            value_col="fev1", metrics=("lln",))["lln"]
        self.assertIn("fev1_pct", df.columns)
        self.assertIn("fev1_lln", df.columns)

    def test_hankinson_compute_with_ethnicity(self):
        df = self.df.copy()
        han = HANKINSON_1999()
        df[["fvc_pct", "fvc_z", "fvc_lln", "fvc_uln"]] = han.compute(
            df, HANKINSON_1999.Parameters.FVC,
            value_col="fvc", ethnicity_col="eth")
        for col in ("fvc_pct", "fvc_z", "fvc_lln", "fvc_uln"):
            self.assertIn(col, df.columns)


class TestReadmeOscillometryExample(unittest.TestCase):
    """README: 'Oscillometry (SCHULZ_2013)'."""

    def setUp(self):
        # SCHULZ_2013 covers adults 40-65; keep the cohort inside that window.
        df = _cohort()
        df["age"] = np.clip(df["age"], 40, 65)
        self.df = df

    def test_schulz_percentiles(self):
        df = self.df.copy()
        s = SCHULZ_2013()
        result = s.compute(
            df, SCHULZ_2013.Parameters.R10,
            weight_col="weight", metrics=("lln", "uln"))
        df["R10_p05"] = result["lln"]
        df["R10_p95"] = result["uln"]
        df["R10_p50"] = df.apply(
            lambda r: s.percentiles(
                r.sex, r.age, r.height, r.weight, SCHULZ_2013.Parameters.R10)[1],
            axis=1)
        # The median should sit between the 5th and 95th percentiles.
        valid = df.dropna(subset=["R10_p05", "R10_p50", "R10_p95"])
        self.assertTrue((valid["R10_p05"] <= valid["R10_p50"]).all())
        self.assertTrue((valid["R10_p50"] <= valid["R10_p95"]).all())


class TestReadmeScalarMethods(unittest.TestCase):
    """README: 'Scalar methods (single patient)'."""

    def test_scalar_calls(self):
        gli = GLI_2012()
        pct = gli.percent(1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.2)
        z = gli.zscore(1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.2)
        lln = gli.lln(1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.2)
        self.assertTrue(pd.notna(pct))
        self.assertTrue(pd.notna(z))
        self.assertTrue(pd.notna(lln))

        bow = BOWERMAN_2022()
        pct_bow = bow.percent(1, 40, 175, BOWERMAN_2022.Parameters.FEV1, 3.2)
        self.assertTrue(pd.notna(pct_bow))

        kus = KUSTER_2008()
        pct_kus = kus.percent(1, 40, 175, 1, KUSTER_2008.Parameters.FEV1, 3.2)
        self.assertTrue(pd.notna(pct_kus))


class TestReadmeNhanesExample(unittest.TestCase):
    """README: 'NHANES III (polynomial equations)'."""

    def setUp(self):
        self.df = _cohort()

    def test_hankinson_all_via_apply(self):
        df = self.df.copy()
        h = HANKINSON_1999()
        df[["fvc_pct", "fvc_z", "fvc_lln", "fvc_uln"]] = df.apply(
            lambda x: pd.Series(
                h.all(x.sex, x.age, x.height, 1, h.Parameters.FVC, x.fvc)
            ),
            axis=1,
        )
        for col in ("fvc_pct", "fvc_z", "fvc_lln", "fvc_uln"):
            self.assertIn(col, df.columns)


class TestReadmeCalogeroExample(unittest.TestCase):
    """README: 'Pediatric oscillometry (CALOGERO_2013)'."""

    def test_scalar_and_compute(self):
        c = CALOGERO_2013()
        pred = c.predicted(sex=0, age=7.0, height=120.0,
                           parameter=CALOGERO_2013.Parameters.Rrs6)
        z = c.zscore(sex=0, age=7.0, height=120.0,
                     parameter=CALOGERO_2013.Parameters.Rrs6, value=8.5)
        uln = c.uln(sex=0, age=7.0, height=120.0,
                    parameter=CALOGERO_2013.Parameters.Rrs6)
        lln_x = c.lln(sex=0, age=7.0, height=120.0,
                      parameter=CALOGERO_2013.Parameters.Xrs6)
        fres_uln = c.uln(sex=0, age=7.0, height=120.0,
                         parameter=CALOGERO_2013.Parameters.Fres)
        for v in (pred, z, uln, lln_x, fres_uln):
            self.assertTrue(pd.notna(v))

        # Children-sized cohort (height is the predictor).
        df = _cohort()
        df["height"] = np.clip(df["height"] - 60, 92, 159)
        df[["rrs6_z", "rrs6_lln", "rrs6_uln"]] = c.compute(
            df, CALOGERO_2013.Parameters.Rrs6,
            value_col="rrs6", metrics=("zscore", "lln", "uln"))
        for col in ("rrs6_z", "rrs6_lln", "rrs6_uln"):
            self.assertIn(col, df.columns)


class TestReadmeRamseyExample(unittest.TestCase):
    """README: 'Multiple breath washout — LCI and FRC (RAMSEY_2024)'."""

    def test_scalar_and_compute(self):
        r = RAMSEY_2024()
        lci_z = r.zscore(sex=0, age=12.0, height=145.0,
                         parameter=RAMSEY_2024.Parameters.LCI, value=8.5)
        lci_uln = r.uln(sex=0, age=12.0, height=145.0,
                        parameter=RAMSEY_2024.Parameters.LCI)
        lci_pct = r.percent(sex=0, age=12.0, height=145.0,
                            parameter=RAMSEY_2024.Parameters.LCI, value=8.5)
        frc_z = r.zscore(sex=1, age=35.0, height=178.0,
                         parameter=RAMSEY_2024.Parameters.FRC, value=3.8)
        frc_lln = r.lln(sex=1, age=35.0, height=178.0,
                        parameter=RAMSEY_2024.Parameters.FRC)
        for v in (lci_z, lci_uln, lci_pct, frc_z, frc_lln):
            self.assertTrue(pd.notna(v))

        df = _cohort()
        df[["lci_z", "lci_lln", "lci_uln"]] = r.compute(
            df, RAMSEY_2024.Parameters.LCI,
            value_col="lci", metrics=("zscore", "lln", "uln"))
        for col in ("lci_z", "lci_lln", "lci_uln"):
            self.assertIn(col, df.columns)


class TestReadmePcdExample(unittest.TestCase):
    """README: 'PCD screening and severity (WODEHOUSE_2003, PCD_SEVERITY)'."""

    def test_wodehouse_classify_and_zscore(self):
        w = WODEHOUSE_2003()
        self.assertEqual(w.classify(nno_ppb=65), "PCD range")
        self.assertEqual(w.classify(nno_ppb=750), "Normal")
        self.assertTrue(pd.notna(w.zscore(65)))

    def test_pcd_severity_staging(self):
        r = RAMSEY_2024()
        gli = GLI_2012()
        sev = PCD_SEVERITY()

        lci_z = r.zscore(sex=0, age=12.0, height=145.0,
                         parameter=RAMSEY_2024.Parameters.LCI, value=9.2)
        fev1_z = gli.zscore(0, 12.0, 145.0, 1, GLI_2012.Parameters.FEV1, 1.4)

        stage = sev.classify(lci_zscore=lci_z, nno_ppb=65, fev1_zscore=fev1_z)
        self.assertIn(stage, {"Mild", "Moderate", "Severe", "Inconclusive"})


class TestReadmeCopdExample(unittest.TestCase):
    """README: 'COPD severity staging'."""

    def setUp(self):
        self.df = _cohort()

    def test_gold_staging(self):
        df = self.df.copy()
        gli = GLI_2012()
        gold = GOLD()
        df["fev1_pct"] = df.apply(
            lambda x: gli.percent(x.sex, x.age, x.height, 1,
                                  gli.Parameters.FEV1, x.fev1),
            axis=1)
        df["GOLD"] = df.apply(lambda x: gold.classify(FEV1p=x.fev1_pct), axis=1)
        df["GOLD"] = pd.Categorical(
            df["GOLD"], categories=gold.get_order(), ordered=True)
        self.assertEqual(len(df["GOLD"]), len(df))


class TestReadmeCompareEquationsExample(unittest.TestCase):
    """README: 'Cross-equation comparison'."""

    def test_compare_single_patient(self):
        patient = pd.Series(
            {"sex": 1, "age": 45.0, "height": 175.0, "ethnicity": 1, "FEV1": 2.8}
        )
        result = compare_equations(
            patient,
            GLI_2012.Parameters.FEV1,
            equations=[GLI_2012(), BOWERMAN_2022(), HANKINSON_1999()],
        )
        self.assertEqual(len(result), 3)
        for col in ("equation", "percent_predicted", "zscore", "applicable"):
            self.assertIn(col, result.columns)

    def test_batch_processing_cohort(self):
        df = _cohort()
        df["patient_id"] = range(len(df))
        results = []
        for _, row in df.iterrows():
            cmp = compare_equations(
                row, GLI_2012.Parameters.FEV1,
                equations=[GLI_2012(), BOWERMAN_2022()])
            cmp["patient_id"] = row["patient_id"]
            results.append(cmp)
        summary = pd.concat(results, ignore_index=True)
        self.assertEqual(len(summary), 2 * len(df))


class TestReadmeCentileChartExample(unittest.TestCase):
    """README: 'Centile chart generation' (requires matplotlib/scipy)."""

    def test_plot_centile_curves(self):
        from matplotlib.figure import Figure

        gli = GLI_2012()
        fig = plot_centile_curves(
            gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=gli.Parameters.FEV1,
            title="FEV1 reference values — male, 175 cm, Caucasian (GLI 2012)",
        )
        self.assertIsInstance(fig, Figure)

    def test_plot_centile_curves_customised(self):
        gli = GLI_2012()
        fig = plot_centile_curves(
            gli,
            sex=0,
            height=165,
            ethnicity=1,
            parameter=gli.Parameters.FVC,
            age_range=(18, 80),
            percentiles=[5, 50, 95],
            figsize=(10, 6),
        )
        self.assertIsNotNone(fig)

    def test_plot_centile_curves_race_neutral(self):
        fig = plot_centile_curves(
            BOWERMAN_2022(),
            sex=1,
            height=175,
            parameter=BOWERMAN_2022.Parameters.FEV1,
        )
        self.assertIsNotNone(fig)


if __name__ == "__main__":
    unittest.main()
