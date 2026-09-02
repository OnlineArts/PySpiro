import unittest

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib_available = True
except ImportError:
    matplotlib_available = False

from pyspiro import (BOWERMAN_2022, GLI_2012, GLI_2017, GLI_2021,
                     KNOX_BROWN_2026, MILLER_2010)
from pyspiro.src.viz import plot_quotient_centiles


@unittest.skipUnless(matplotlib_available, "matplotlib not installed")
class TestPlotQuotientCentiles(unittest.TestCase):

    def setUp(self):
        self.equation = BOWERMAN_2022()
        self.quotient = KNOX_BROWN_2026()

    def tearDown(self):
        plt.close("all")

    def _plot(self, **overrides):
        kwargs = dict(sex=1, height=175, parameter=BOWERMAN_2022.Parameters.FEV1)
        kwargs.update(overrides)
        return plot_quotient_centiles(self.equation, self.quotient, **kwargs)

    # ── Basic construction ─────────────────────────────────────────────────

    def test_creates_figure(self):
        self.assertIsNotNone(self._plot())

    def test_plots_one_line_per_centile_plus_band_grid(self):
        fig = self._plot(percentiles=[5, 50, 95], bands=[])
        self.assertEqual(len(fig.axes[0].get_lines()), 3)

    def test_band_grid_adds_horizontal_lines(self):
        with_bands = self._plot(percentiles=[50], bands=[1, 2, 3])
        self.assertEqual(len(with_bands.axes[0].get_lines()), 4)

    def test_empty_bands_draws_no_grid(self):
        fig = self._plot(percentiles=[50], bands=[])
        self.assertEqual(len(fig.axes[0].get_lines()), 1)

    def test_custom_figsize(self):
        fig = self._plot(figsize=(9, 4))
        self.assertEqual(tuple(fig.get_size_inches()), (9, 4))

    def test_custom_title(self):
        fig = self._plot(title="Custom")
        self.assertEqual(fig.axes[0].get_title(), "Custom")

    def test_auto_title_names_both_classes(self):
        title = self._plot().axes[0].get_title()
        self.assertIn("BOWERMAN_2022", title)
        self.assertIn("KNOX_BROWN_2026", title)

    def test_plots_on_existing_axes(self):
        fig, ax = plt.subplots()
        self.assertEqual(self._plot(ax=ax), fig)

    def test_y_axis_starts_at_zero(self):
        # A quotient is a ratio to a fixed positive value; a truncated y-axis
        # would misrepresent how far a measurement sits from the 1st percentile.
        self.assertEqual(self._plot().axes[0].get_ylim()[0], 0)

    def test_y_label_reports_the_denominator(self):
        self.assertIn("0.50", self._plot().axes[0].get_ylabel())
        self.assertIn("0.40", self._plot(sex=0, height=163).axes[0].get_ylabel())

    # ── The rescaling itself ───────────────────────────────────────────────

    def test_curve_is_the_equation_centile_divided_by_the_denominator(self):
        from scipy import stats

        fig = self._plot(percentiles=[5], bands=[], age_range=(25, 80))
        ages, quotients = fig.axes[0].get_lines()[0].get_data()

        denominator = self.quotient.percentile1(KNOX_BROWN_2026.Parameters.FEV1, sex=1)
        z = stats.norm.ppf(0.05)
        expected = []
        for age in ages:
            l, m, s = self.equation.lms(1, float(age), 175.0,
                                        BOWERMAN_2022.Parameters.FEV1, 0)
            expected.append(m * ((1 + z * l * s) ** (1 / l)) / denominator)
        np.testing.assert_allclose(quotients, expected, rtol=1e-12)

    def test_fifth_centile_tracks_the_equations_own_lln(self):
        # Not exact: lln() hardcodes z = -1.645, the centile uses the exact 5th
        # percentile quantile (-1.64485), so the two differ in the 5th decimal.
        fig = self._plot(percentiles=[5], bands=[], age_range=(25, 80))
        ages, quotients = fig.axes[0].get_lines()[0].get_data()

        denominator = self.quotient.percentile1(KNOX_BROWN_2026.Parameters.FEV1, sex=1)
        expected = [
            self.equation.lln(sex=1, age=float(age), height=175.0,
                              parameter=BOWERMAN_2022.Parameters.FEV1, value=0) / denominator
            for age in ages
        ]
        np.testing.assert_allclose(quotients, expected, rtol=1e-3)

    def test_female_denominator_differs_from_male(self):
        male = self._plot(percentiles=[50], bands=[]).axes[0].get_lines()[0].get_ydata()
        female = self._plot(sex=0, percentiles=[50], bands=[]).axes[0].get_lines()[0].get_ydata()
        self.assertFalse(np.allclose(male, female))

    def test_lln_as_quotient_falls_with_age(self):
        # The paper's 1st percentile is age-stable; the quotient it produces is
        # not age-neutral to read. Guards the interpretive caveat in the docstring.
        fig = self._plot(percentiles=[5], bands=[], age_range=(20, 90))
        curve = fig.axes[0].get_lines()[0].get_ydata()
        self.assertGreater(curve[0], curve[-1])
        self.assertGreater(curve[0] / curve[-1], 1.5)

    # ── Parameter resolution ───────────────────────────────────────────────

    def test_resolves_quotient_parameter_by_name(self):
        by_name = self._plot(percentiles=[50], bands=[])
        explicit = self._plot(percentiles=[50], bands=[],
                              quotient_parameter=KNOX_BROWN_2026.Parameters.FEV1)
        np.testing.assert_allclose(by_name.axes[0].get_lines()[0].get_ydata(),
                                   explicit.axes[0].get_lines()[0].get_ydata())

    def test_unmatched_name_raises(self):
        # GLI_2017 calls the SI transfer factor TLCO; the quotient calls it DLCO_SI.
        with self.assertRaises(ValueError):
            plot_quotient_centiles(GLI_2017(), self.quotient, sex=1, height=175,
                                   parameter=GLI_2017.Parameters.TLCO)

    def test_explicit_quotient_parameter_bridges_the_naming_gap(self):
        fig = plot_quotient_centiles(
            GLI_2017(), self.quotient, sex=1, height=175,
            parameter=GLI_2017.Parameters.TLCO,
            quotient_parameter=KNOX_BROWN_2026.Parameters.DLCO_SI,
            age_range=(20, 90))
        self.assertIn("1.60", fig.axes[0].get_ylabel())

    def test_missing_sex_for_sex_specific_parameter_raises(self):
        with self.assertRaises(ValueError):
            self._plot(sex=None)

    # ── Other equation families ────────────────────────────────────────────

    def test_ethnicity_stratified_equation(self):
        fig = plot_quotient_centiles(GLI_2012(), self.quotient, sex=1, height=175,
                                     parameter=GLI_2012.Parameters.FVC, ethnicity=1)
        self.assertIn("1.50", fig.axes[0].get_ylabel())

    def test_static_lung_volumes(self):
        fig = plot_quotient_centiles(GLI_2021(), self.quotient, sex=0, height=163,
                                     parameter=GLI_2021.Parameters.TLC)
        self.assertIn("2.30", fig.axes[0].get_ylabel())

    def test_sex_neutral_parameter_needs_no_sex_specific_denominator(self):
        fig = plot_quotient_centiles(BOWERMAN_2022(), self.quotient, sex=1, height=175,
                                     parameter=BOWERMAN_2022.Parameters.FEV1FVC)
        self.assertIn("0.15", fig.axes[0].get_ylabel())

    # ── Other quotients ────────────────────────────────────────────────────

    def test_accepts_any_quotient_implementation(self):
        # MILLER_2010 names its member FEV1Q; the equation's FEV1 still resolves.
        fig = plot_quotient_centiles(BOWERMAN_2022(), MILLER_2010(), sex=1, height=175,
                                     parameter=BOWERMAN_2022.Parameters.FEV1)
        self.assertIn("0.50", fig.axes[0].get_ylabel())
        self.assertIn("MILLER_2010", fig.axes[0].get_title())

    def test_the_two_quotients_draw_the_same_fev1_curve(self):
        shared = dict(sex=0, height=163, parameter=BOWERMAN_2022.Parameters.FEV1,
                      percentiles=[50], bands=[])
        knox = plot_quotient_centiles(BOWERMAN_2022(), KNOX_BROWN_2026(), **shared)
        miller = plot_quotient_centiles(BOWERMAN_2022(), MILLER_2010(), **shared)
        np.testing.assert_allclose(knox.axes[0].get_lines()[0].get_ydata(),
                                   miller.axes[0].get_lines()[0].get_ydata())


if __name__ == "__main__":
    unittest.main()
