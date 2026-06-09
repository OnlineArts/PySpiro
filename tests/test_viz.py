import unittest
import pandas as pd
import numpy as np

try:
    import matplotlib.pyplot as plt
    matplotlib_available = True
except ImportError:
    matplotlib_available = False

from pyspiro import GLI_2012, BOWERMANN_2022
from pyspiro.viz import plot_centile_curves


@unittest.skipUnless(matplotlib_available, "matplotlib not installed")
class TestPlotCentileCurves(unittest.TestCase):

    def setUp(self):
        self.gli = GLI_2012()
        self.bowermann = BOWERMANN_2022()

    def tearDown(self):
        plt.close('all')

    def test_plot_creates_figure(self):
        fig = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1
        )
        self.assertIsNotNone(fig)

    def test_plot_with_custom_percentiles(self):
        fig = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1,
            percentiles=[10, 50, 90]
        )
        self.assertIsNotNone(fig)

    def test_plot_with_custom_age_range(self):
        fig = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1,
            age_range=(20, 60)
        )
        self.assertIsNotNone(fig)

    def test_plot_with_custom_title(self):
        title = "Custom Title"
        fig = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1,
            title=title
        )
        ax = fig.axes[0]
        self.assertEqual(ax.get_title(), title)

    def test_plot_with_custom_figsize(self):
        figsize = (8, 5)
        fig = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1,
            figsize=figsize
        )
        self.assertEqual(fig.get_size_inches()[0], figsize[0])
        self.assertEqual(fig.get_size_inches()[1], figsize[1])

    def test_plot_female_male_differ(self):
        """Percentile curves should differ between sexes"""
        fig_male = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1
        )
        fig_female = plot_centile_curves(
            self.gli,
            sex=0,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1
        )
        # Check that axes have different Y values
        ax_m = fig_male.axes[0]
        ax_f = fig_female.axes[0]
        self.assertNotEqual(
            ax_m.get_lines()[0].get_ydata()[50],
            ax_f.get_lines()[0].get_ydata()[50]
        )
        plt.close(fig_male)
        plt.close(fig_female)

    def test_plot_bowermann_no_ethnicity(self):
        """Race-neutral equations should not require ethnicity"""
        fig = plot_centile_curves(
            self.bowermann,
            sex=1,
            height=175,
            parameter=self.bowermann.Parameters.FEV1
        )
        self.assertIsNotNone(fig)

    def test_plot_on_existing_axes(self):
        fig, ax = plt.subplots()
        result_fig = plot_centile_curves(
            self.gli,
            sex=1,
            height=175,
            ethnicity=1,
            parameter=self.gli.Parameters.FEV1,
            ax=ax
        )
        self.assertEqual(result_fig, fig)


@unittest.skipUnless(not matplotlib_available, "matplotlib is installed")
class TestPlotCentileCurvesNoMatplotlib(unittest.TestCase):

    def test_raises_import_error_without_matplotlib(self):
        gli = GLI_2012()
        with self.assertRaises(ImportError):
            plot_centile_curves(
                gli,
                sex=1,
                height=175,
                ethnicity=1,
                parameter=gli.Parameters.FEV1
            )


if __name__ == "__main__":
    unittest.main()
