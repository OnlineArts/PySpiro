import math
import unittest

import pandas as pd

from pyspiro import ALQEREM_2021

M = 1
F = 0

P = ALQEREM_2021.Parameters

# ---------------------------------------------------------------------------
# Al-Qerem W. Spirometry reference equations for children from a Middle Eastern
# population. Int J Clin Pract 2021;75(11):e14598. DOI: 10.1111/ijcp.14598
#
# Twenty-four subjects drawn from the author's own SPSS analysis file, spanning
# both sexes and the full age and height range of the cohort.  Every age lands
# exactly on the 0.25-year spline grid, so no lookup rounding is involved.
#
# mu_*, z_* and lln_* are the values the author stored, not values recomputed
# from the module.  They therefore test the module against the fitted model
# rather than against itself, and they are the only such anchor that survives:
# the source data set is not distributed with this package.
#
# Agreement is limited to about 1e-3 by the 5-6 decimal places to which the
# coefficients are printed in Tables 2 and 3.
# ---------------------------------------------------------------------------
SUBJECTS = [
    dict(sex=M, age=6.00, height=104,
         fev1=0.87, fvc=0.89, ratio=97.75, fef=1.62,
         mu_fev1=0.934793, mu_fvc=0.945576, mu_ratio=93.576602, mu_fef=1.232947,
         z_fev1=-0.500524, z_fvc=-0.453900, z_ratio=0.538639, z_fef=1.134176,
         lln_fev1=0.733538, lln_fvc=0.766584, lln_ratio=78.457454, lln_fef=0.741629),
    dict(sex=M, age=8.00, height=122,
         fev1=1.28, fvc=1.29, ratio=99.22, fef=1.86,
         mu_fev1=1.407610, mu_fvc=1.546613, mu_ratio=89.787540, mu_fef=1.700468,
         z_fev1=-0.694899, z_fvc=-1.409951, z_ratio=1.378916, z_fef=0.377234,
         lln_fev1=1.121740, lln_fvc=1.253848, lln_ratio=75.777354, lln_fef=1.081500),
    dict(sex=M, age=10.00, height=141,
         fev1=1.67, fvc=1.95, ratio=85.64, fef=1.78,
         mu_fev1=2.043297, mu_fvc=2.393764, mu_ratio=88.192254, mu_fef=2.339656,
         z_fev1=-1.510388, z_fvc=-1.604926, z_ratio=-0.348995, z_fef=-1.118175,
         lln_fev1=1.640240, lln_fvc=1.940639, lln_ratio=74.798563, lln_fef=1.544186),
    dict(sex=M, age=11.25, height=145,
         fev1=2.81, fvc=3.08, ratio=91.23, fef=3.55,
         mu_fev1=2.260911, mu_fvc=2.653183, mu_ratio=88.139191, mu_fef=2.592442,
         z_fev1=1.638103, z_fvc=1.050365, z_ratio=0.453493, z_fef=1.514600,
         lln_fev1=1.823584, lln_fvc=2.150951, lln_ratio=74.943609, lln_fef=1.741706),
    dict(sex=M, age=14.00, height=172,
         fev1=2.97, fvc=3.38, ratio=87.87, fef=3.62,
         mu_fev1=3.729256, mu_fvc=4.393217, mu_ratio=86.219759, mu_fef=4.050165,
         z_fev1=-1.891730, z_fvc=-2.088320, z_ratio=0.250265, z_fef=-0.525493,
         lln_fev1=3.057671, lln_fvc=3.561606, lln_ratio=73.649789, lln_fef=2.804515),
    dict(sex=M, age=14.50, height=177,
         fev1=4.02, fvc=4.24, ratio=94.81, fef=4.76,
         mu_fev1=4.062538, mu_fvc=4.779284, mu_ratio=86.086472, mu_fef=4.380319,
         z_fev1=-0.087160, z_fvc=-0.913267, z_ratio=1.427975, z_fef=0.406371,
         lln_fev1=3.344389, lln_fvc=3.874593, lln_ratio=73.589291, lln_fef=3.046933),
    dict(sex=M, age=15.50, height=170,
         fev1=3.99, fvc=4.63, ratio=86.18, fef=4.08,
         mu_fev1=3.833193, mu_fvc=4.368459, mu_ratio=87.811719, mu_fef=4.294824,
         z_fev1=0.343739, z_fvc=0.420572, z_ratio=-0.238314, z_fef=-0.249747,
         lln_fev1=3.182267, lln_fvc=3.541535, lln_ratio=75.166870, lln_fef=3.012707),
    dict(sex=M, age=16.25, height=175,
         fev1=4.38, fvc=4.38, ratio=100.00, fef=6.30,
         mu_fev1=4.204891, mu_fvc=4.770850, mu_ratio=88.492031, mu_fef=4.724330,
         z_fev1=0.360799, z_fvc=-0.645312, z_ratio=1.904290, z_fef=1.494785,
         lln_fev1=3.512278, lln_fvc=3.867756, lln_ratio=75.822105, lln_fef=3.333261),
    dict(sex=M, age=16.50, height=177,
         fev1=4.94, fvc=4.98, ratio=99.20, fef=8.00,
         mu_fev1=4.352896, mu_fvc=4.934549, mu_ratio=88.730532, mu_fef=4.893582,
         z_fev1=1.115527, z_fvc=0.067287, z_ratio=1.712985, z_fef=2.641652,
         lln_fev1=3.642993, lln_fvc=4.000468, lln_ratio=76.049985, lln_fef=3.459051),
    dict(sex=M, age=16.75, height=186,
         fev1=5.12, fvc=5.50, ratio=93.09, fef=5.43,
         mu_fev1=4.924492, mu_fvc=5.644824, mu_ratio=88.338607, mu_fef=5.435914,
         z_fev1=0.351390, z_fvc=-0.192756, z_ratio=0.740716, z_fef=-0.005454,
         lln_fev1=4.129188, lln_fvc=4.576291, lln_ratio=75.737101, lln_fef=3.849337),
    dict(sex=M, age=17.25, height=180,
         fev1=4.19, fvc=4.65, ratio=90.11, fef=5.45,
         mu_fev1=4.636709, mu_fvc=5.215162, mu_ratio=89.814227, mu_fef=5.272262,
         z_fev1=-0.954480, z_fvc=-0.873616, z_ratio=0.043159, z_fef=0.168261,
         lln_fev1=3.902024, lln_fvc=4.227962, lln_ratio=77.047907, lln_fef=3.746503),
    dict(sex=M, age=17.75, height=180,
         fev1=3.70, fvc=4.90, ratio=75.51, fef=3.07,
         mu_fev1=4.710312, mu_fvc=5.252163, mu_ratio=90.773814, mu_fef=5.428623,
         z_fev1=-2.379247, z_fvc=-0.521460, z_ratio=-1.904516, z_fef=-2.687340,
         lln_fev1=3.977568, lln_fvc=4.257959, lln_ratio=77.915799, lln_fef=3.870534),
    dict(sex=F, age=6.25, height=106,
         fev1=1.11, fvc=1.13, ratio=98.23, fef=1.63,
         mu_fev1=0.940387, mu_fvc=0.989934, mu_ratio=94.734189, mu_fef=1.359626,
         z_fev1=1.371231, z_fvc=1.003709, z_ratio=0.624532, z_fef=0.901889,
         lln_fev1=0.771101, lln_fvc=0.805928, lln_ratio=83.288566, lln_fef=0.940616),
    dict(sex=F, age=8.25, height=128,
         fev1=1.89, fvc=2.02, ratio=93.56, fef=2.50,
         mu_fev1=1.520669, mu_fvc=1.650847, mu_ratio=92.544650, mu_fef=1.979492,
         z_fev1=1.797361, z_fvc=1.514166, z_ratio=0.180015, z_fef=1.173007,
         lln_fev1=1.246922, lln_fvc=1.343993, lln_ratio=81.363564, lln_fef=1.369451),
    dict(sex=F, age=10.50, height=154,
         fev1=2.07, fvc=2.41, ratio=85.89, fef=2.40,
         mu_fev1=2.405720, mu_fvc=2.693317, mu_ratio=90.455664, mu_fef=2.815674,
         z_fev1=-1.245355, z_fvc=-0.875877, z_ratio=-0.757552, z_fef=-0.742610,
         lln_fev1=1.972647, lln_fvc=2.192691, lln_ratio=79.526965, lln_fef=1.947938),
    dict(sex=F, age=12.25, height=146,
         fev1=2.23, fvc=2.51, ratio=88.84, fef=2.43,
         mu_fev1=2.307139, mu_fvc=2.549191, mu_ratio=90.989558, mu_fef=2.853342,
         z_fev1=-0.281563, z_fvc=-0.120266, z_ratio=-0.367336, z_fef=-0.746513,
         lln_fev1=1.891812, lln_fvc=2.075355, lln_ratio=79.996355, lln_fef=1.973998),
    dict(sex=F, age=14.00, height=166,
         fev1=3.50, fvc=3.99, ratio=87.72, fef=3.85,
         mu_fev1=3.129109, mu_fvc=3.534379, mu_ratio=89.568210, mu_fef=3.581216,
         z_fev1=0.926589, z_fvc=0.921257, z_ratio=-0.322964, z_fef=0.352161,
         lln_fev1=2.565813, lln_fvc=2.877418, lln_ratio=78.746732, lln_fef=2.477556),
    dict(sex=F, age=14.50, height=158,
         fev1=2.73, fvc=3.34, ratio=81.74, fef=2.46,
         mu_fev1=2.881972, mu_fvc=3.222442, mu_ratio=90.087980, mu_fef=3.430508,
         z_fev1=-0.448594, z_fvc=0.275903, z_ratio=-1.312757, z_fef=-1.495082,
         lln_fev1=2.363165, lln_fvc=2.623463, lln_ratio=79.203704, lln_fef=2.373293),
    dict(sex=F, age=15.00, height=158,
         fev1=2.70, fvc=3.06, ratio=88.24, fef=2.89,
         mu_fev1=2.921760, mu_fvc=3.264815, mu_ratio=90.078405, mu_fef=3.490781,
         z_fev1=-0.653737, z_fvc=-0.506829, z_ratio=-0.320207, z_fef=-0.873094,
         lln_fev1=2.395791, lln_fvc=2.657960, lln_ratio=79.195286, lln_fef=2.414991),
    dict(sex=F, age=15.50, height=155,
         fev1=2.57, fvc=2.94, ratio=87.41, fef=3.37,
         mu_fev1=2.851965, mu_fvc=3.173164, mu_ratio=90.275498, mu_fef=3.466994,
         z_fev1=-0.862316, z_fvc=-0.598127, z_ratio=-0.488278, z_fef=-0.135356,
         lln_fev1=2.338560, lln_fvc=2.583345, lln_ratio=79.368567, lln_fef=2.398534),
    dict(sex=F, age=16.25, height=156,
         fev1=2.31, fvc=2.70, ratio=85.56, fef=2.48,
         mu_fev1=2.943736, mu_fvc=3.276344, mu_ratio=90.192857, mu_fef=3.580525,
         z_fev1=-2.009903, z_fvc=-1.544681, z_ratio=-0.771009, z_fef=-1.640107,
         lln_fev1=2.413810, lln_fvc=2.667347, lln_ratio=79.295911, lln_fef=2.477077),
    dict(sex=F, age=16.75, height=155,
         fev1=2.39, fvc=2.64, ratio=90.53, fef=2.78,
         mu_fev1=2.942844, mu_fvc=3.269429, mu_ratio=90.253548, mu_fef=3.607929,
         z_fev1=-1.724757, z_fvc=-1.712762, z_ratio=0.049549, z_fef=-1.188383,
         lln_fev1=2.413079, lln_fvc=2.661717, lln_ratio=79.349269, lln_fef=2.496036),
    dict(sex=F, age=17.00, height=167,
         fev1=3.17, fvc=3.26, ratio=97.24, fef=3.82,
         mu_fev1=3.424667, mu_fvc=3.858324, mu_ratio=89.449547, mu_fef=3.986331,
         z_fev1=-0.639968, z_fvc=-1.339998, z_ratio=1.577100, z_fef=-0.202744,
         lln_fev1=2.808165, lln_fvc=3.141149, lln_ratio=78.642406, lln_fef=2.757822),
    dict(sex=F, age=17.75, height=163,
         fev1=3.22, fvc=3.81, ratio=84.51, fef=3.20,
         mu_fev1=3.323825, mu_fvc=3.724302, mu_ratio=89.696657, mu_fef=3.955470,
         z_fev1=-0.262752, z_fvc=0.175533, z_ratio=-0.858787, z_fef=-0.975397,
         lln_fev1=2.725477, lln_fvc=3.032040, lln_ratio=78.859660, lln_fef=2.736472),
]

# parameter -> (measured key, mu key, z key, lln key)
KEYS = {
    P.FEV1:     ('fev1',  'mu_fev1',  'z_fev1',  'lln_fev1'),
    P.FVC:      ('fvc',   'mu_fvc',   'z_fvc',   'lln_fvc'),
    P.FEV1FVC:  ('ratio', 'mu_ratio', 'z_ratio', 'lln_ratio'),
    P.FEF25_75: ('fef',   'mu_fef',   'z_fef',   'lln_fef'),
}


def mu(eq, sex, age, height, parameter):
    """Predicted median.  percent() rounds to 2 dp, so read M off lms() instead."""
    return eq.lms(sex, age, height, parameter.value, 1.0)[1]


class TestALQerem2021Instantiation(unittest.TestCase):

    def test_instantiation(self):
        self.assertIsNotNone(ALQEREM_2021())

    def test_is_an_lms_reference(self):
        from pyspiro.src.reference import LMSReference
        self.assertIsInstance(ALQEREM_2021(), LMSReference)

    def test_parameters(self):
        codes = {p.name: p.value for p in P}
        self.assertEqual(codes, {'FEV1': 1, 'FVC': 2, 'FEV1FVC': 3, 'FEF25_75': 4})

    def test_takes_no_ethnicity_argument(self):
        import inspect
        self.assertNotIn('ethnicity', inspect.signature(ALQEREM_2021().lms).parameters)


class TestALQerem2021SplineTables(unittest.TestCase):
    """Tables A3 (FEV1), A4 (FEV1/FVC) and A5 (FEF25-75), males only."""

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_age_range_is_the_extent_of_the_lookup_table(self):
        self.assertEqual(self.eq._age_range, (6.0, 17.75))

    def test_forty_eight_rows_in_quarter_year_steps(self):
        ages = list(self.eq._lookup.index)
        self.assertEqual(len(ages), 48)
        self.assertEqual(ages[0], 6.0)
        self.assertEqual(ages[-1], 17.75)
        self.assertTrue(all(round(b - a, 10) == 0.25 for a, b in zip(ages, ages[1:])))

    def test_table_a3_endpoints(self):
        self.assertAlmostEqual(self.eq._lookup['FEV1_males_Mspline'].loc[6.0], 0.072391, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEV1_males_Sspline'].loc[6.0], -0.05671, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEV1_males_Mspline'].loc[17.75], 0.023698, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEV1_males_Sspline'].loc[17.75], -0.0429, places=6)

    def test_table_a4_endpoints(self):
        self.assertAlmostEqual(self.eq._lookup['FEV1FVC_males_Mspline'].loc[6.0], 0.038616, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEV1FVC_males_Sspline'].loc[6.0], 7.06e-05, places=8)
        self.assertAlmostEqual(self.eq._lookup['FEV1FVC_males_Mspline'].loc[17.75], 0.025837, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEV1FVC_males_Sspline'].loc[17.75], 3.18e-05, places=8)

    def test_table_a5_endpoints(self):
        self.assertAlmostEqual(self.eq._lookup['FEF25_75_males_Mspline'].loc[6.0], 0.122069, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEF25_75_males_Sspline'].loc[6.0], -0.00013, places=7)
        self.assertAlmostEqual(self.eq._lookup['FEF25_75_males_Mspline'].loc[17.75], 0.051996, places=6)
        self.assertAlmostEqual(self.eq._lookup['FEF25_75_males_Sspline'].loc[17.75], -3.92e-05, places=8)

    def test_male_fvc_has_no_spline(self):
        # Table 2 gives FVC as a closed form with no MSpline or SSpline term.
        self.assertTrue((self.eq._lookup['FVC_males_Mspline'] == 0).all())
        self.assertTrue((self.eq._lookup['FVC_males_Sspline'] == 0).all())

    def test_no_female_equation_has_a_spline(self):
        # Table 3 gives all four female equations in closed form.
        female = [c for c in self.eq._lookup.columns if 'females' in c]
        self.assertEqual(len(female), 12)
        for col in female:
            self.assertTrue((self.eq._lookup[col] == 0).all(), col)

    def test_lspline_is_zero_everywhere(self):
        # Nu is a plain linear function of log(age); the published Lspline column is 0.
        for col in [c for c in self.eq._lookup.columns if 'Lspline' in c]:
            self.assertTrue((self.eq._lookup[col] == 0).all(), col)


class TestALQerem2021MaleFVCSignCorrection(unittest.TestCase):
    """Table 2 prints "- 0.24743 * log (age)" for male FVC.  The sign must be positive.

    As printed the equation returns an FVC far below the FEV1 that the same table
    predicts for the same child.  The corrected form reproduces the author's own
    predicted FVC exactly.
    """

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_module_uses_the_positive_age_coefficient(self):
        self.assertAlmostEqual(mu(self.eq, M, 12, 150, P.FVC), 2.947977, places=5)

    def test_module_rejects_the_printed_negative_age_coefficient(self):
        printed = math.exp(-12.74371 + 2.63639 * math.log(150) - 0.24743 * math.log(12))
        self.assertAlmostEqual(printed, 0.861947, places=5)
        self.assertNotAlmostEqual(mu(self.eq, M, 12, 150, P.FVC), printed, places=2)

    def test_printed_coefficient_would_put_fvc_below_fev1(self):
        printed = math.exp(-12.74371 + 2.63639 * math.log(150) - 0.24743 * math.log(12))
        self.assertLess(printed, mu(self.eq, M, 12, 150, P.FEV1))

    def test_second_worked_point(self):
        self.assertAlmostEqual(mu(self.eq, M, 16, 170, P.FVC), 4.402970, places=5)

    def test_male_fvc_rises_with_age_at_fixed_height(self):
        heights = (130, 150, 170)
        for h in heights:
            with self.subTest(height=h):
                self.assertLess(mu(self.eq, M, 8, h, P.FVC), mu(self.eq, M, 16, h, P.FVC))


class TestALQerem2021MaleFEV1FVCInterceptCorrection(unittest.TestCase):
    """Table 2 prints an intercept of 4.5057904 for male FEV1/FVC.

    Paired with the Table A4 age-spline that underestimates the author's own
    predicted ratio by a constant 0.104%.  Holding the two published slopes fixed,
    the intercept their data implies is 4.5068298.  Intercept and Mspline column
    are confounded up to an additive constant, so the published A4 table requires
    the corrected intercept.
    """

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_module_uses_the_corrected_intercept(self):
        self.assertAlmostEqual(mu(self.eq, M, 15, 170, P.FEV1FVC), 87.192588, places=5)

    def test_module_rejects_the_printed_intercept(self):
        mspline = self.eq._lookup['FEV1FVC_males_Mspline'].loc[15.0]
        printed = math.exp(4.5057904 - 0.0010421 * 170 + 0.0567665 * math.log(15) + mspline)
        self.assertAlmostEqual(printed, 87.102007, places=5)
        self.assertNotAlmostEqual(mu(self.eq, M, 15, 170, P.FEV1FVC), printed, places=3)

    def test_the_two_intercepts_differ_by_about_one_tenth_of_a_percent(self):
        ratio = math.exp(4.5068298 - 4.5057904)
        self.assertAlmostEqual(ratio, 1.00104, places=5)

    def test_male_ratio_takes_height_untransformed(self):
        # The one equation whose height term is not log(height).
        c = self.eq._coefficients['FEV1FVC_males']
        self.assertEqual(c.loc['h_log'], 0)
        for other in ('FEV1_males', 'FVC_males', 'FEF25_75_males',
                      'FEV1_females', 'FVC_females', 'FEV1FVC_females', 'FEF25_75_females'):
            self.assertEqual(self.eq._coefficients[other].loc['h_log'], 1, other)


class TestALQerem2021FemaleClosedForm(unittest.TestCase):
    """Table 3 has no spline terms, so every female prediction is a closed form."""

    def setUp(self):
        self.eq = ALQEREM_2021()
        self.lh, self.la = math.log(150), math.log(12)

    def test_fev1(self):
        expected = math.exp(-9.91054 + 1.95304 * self.lh + 0.40445 * self.la)
        self.assertAlmostEqual(mu(self.eq, F, 12, 150, P.FEV1), expected, places=9)
        self.assertAlmostEqual(expected, 2.411989, places=5)

    def test_fvc(self):
        expected = math.exp(-10.71678 + 2.14445 * self.lh + 0.38534 * self.la)
        self.assertAlmostEqual(mu(self.eq, F, 12, 150, P.FVC), expected, places=9)
        self.assertAlmostEqual(expected, 2.679984, places=5)

    def test_fev1fvc(self):
        expected = math.exp(5.113524 - 0.119376 * self.lh - 0.003135 * self.la)
        self.assertAlmostEqual(mu(self.eq, F, 12, 150, P.FEV1FVC), expected, places=9)
        self.assertAlmostEqual(expected, 90.702436, places=5)

    def test_fef25_75(self):
        expected = math.exp(-6.39575 + 1.23545 * self.lh + 0.51376 * self.la)
        self.assertAlmostEqual(mu(self.eq, F, 12, 150, P.FEF25_75), expected, places=9)
        self.assertAlmostEqual(expected, 2.919128, places=5)

    def test_female_sigma_and_nu_are_constant(self):
        for parameter, sigma, nu in ((P.FEV1, math.exp(-2.11359), -0.01264),
                                     (P.FVC, math.exp(-2.04685), -0.3144),
                                     (P.FEV1FVC, math.exp(-2.77845), 3.7365),
                                     (P.FEF25_75, math.exp(-1.56799), 0.3942)):
            with self.subTest(parameter=parameter.name):
                young = self.eq.lms(F, 7, 120, parameter.value, 1.0)
                old = self.eq.lms(F, 17, 170, parameter.value, 1.0)
                self.assertAlmostEqual(young[0], nu, places=9)
                self.assertAlmostEqual(old[0], nu, places=9)
                self.assertAlmostEqual(young[2], sigma, places=9)
                self.assertAlmostEqual(old[2], sigma, places=9)


class TestALQerem2021NuAndSigma(unittest.TestCase):
    """Table 2: male nu and sigma vary with log(age); FVC is the exception."""

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_male_fev1_nu(self):
        nu = self.eq.lms(M, 12, 150, P.FEV1.value, 1.0)[0]
        self.assertAlmostEqual(nu, 1.4157 - 0.6146 * math.log(12), places=9)
        self.assertAlmostEqual(nu, -0.111524, places=6)

    def test_male_fev1fvc_nu(self):
        nu = self.eq.lms(M, 12, 150, P.FEV1FVC.value, 1.0)[0]
        self.assertAlmostEqual(nu, 2.3252 + 0.1598 * math.log(12), places=9)

    def test_male_fef25_75_nu(self):
        nu = self.eq.lms(M, 12, 150, P.FEF25_75.value, 1.0)[0]
        self.assertAlmostEqual(nu, 1.2667 - 0.3456 * math.log(12), places=9)

    def test_male_fvc_nu_and_sigma_are_constant(self):
        young = self.eq.lms(M, 7, 120, P.FVC.value, 1.0)
        old = self.eq.lms(M, 17, 170, P.FVC.value, 1.0)
        self.assertAlmostEqual(young[0], -0.5959, places=9)
        self.assertAlmostEqual(old[0], -0.5959, places=9)
        self.assertAlmostEqual(young[2], math.exp(-1.99593), places=9)
        self.assertAlmostEqual(old[2], math.exp(-1.99593), places=9)

    def test_male_fev1_sigma_includes_the_a3_sspline(self):
        sspline = self.eq._lookup['FEV1_males_Sspline'].loc[12.0]
        expected = math.exp(-1.38973 - 0.28249 * math.log(12) + sspline)
        self.assertAlmostEqual(self.eq.lms(M, 12, 150, P.FEV1.value, 1.0)[2], expected, places=9)


class TestALQerem2021AgainstAuthorsDataset(unittest.TestCase):
    """Reproduce the predicted values, z-scores and LLNs the author stored.

    Coefficients are printed to 5-6 decimals, which caps agreement near 1e-3.
    """

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_predicted_median(self):
        for s in SUBJECTS:
            for parameter, (_, mu_key, _, _) in KEYS.items():
                with self.subTest(sex=s['sex'], age=s['age'], parameter=parameter.name):
                    self.assertAlmostEqual(mu(self.eq, s['sex'], s['age'], s['height'], parameter),
                                           s[mu_key], delta=1e-3)

    def test_zscore(self):
        for s in SUBJECTS:
            for parameter, (y_key, _, z_key, _) in KEYS.items():
                with self.subTest(sex=s['sex'], age=s['age'], parameter=parameter.name):
                    z = self.eq.zscore(s['sex'], s['age'], s['height'], parameter.value, s[y_key])
                    self.assertAlmostEqual(z, s[z_key], delta=1e-3)

    def test_lln(self):
        for s in SUBJECTS:
            for parameter, (y_key, _, _, lln_key) in KEYS.items():
                with self.subTest(sex=s['sex'], age=s['age'], parameter=parameter.name):
                    lln = self.eq.lln(s['sex'], s['age'], s['height'], parameter.value, s[y_key])
                    self.assertAlmostEqual(lln, s[lln_key], delta=1e-3)

    def test_percent(self):
        for s in SUBJECTS:
            for parameter, (y_key, mu_key, _, _) in KEYS.items():
                with self.subTest(sex=s['sex'], age=s['age'], parameter=parameter.name):
                    pct = self.eq.percent(s['sex'], s['age'], s['height'], parameter.value, s[y_key])
                    self.assertAlmostEqual(pct, s[y_key] / s[mu_key] * 100, delta=0.1)


# Age paired with a height a child of that age plausibly has.  The equations
# extrapolate poorly to combinations the cohort never contained: at 17.75 y and
# 110 cm they return an FEV1 above the FVC.  Nothing in the paper bounds height,
# so the module does not either.
PLAUSIBLE = ((6, 115), (9, 132), (12, 150), (15, 165), (17.75, 172))


class TestALQerem2021Physiology(unittest.TestCase):

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_predicted_fvc_exceeds_predicted_fev1(self):
        for sex in (M, F):
            for age, height in PLAUSIBLE:
                with self.subTest(sex=sex, age=age, height=height):
                    self.assertLess(mu(self.eq, sex, age, height, P.FEV1),
                                    mu(self.eq, sex, age, height, P.FVC))

    def test_predicted_ratio_is_a_plausible_percentage(self):
        for sex in (M, F):
            for age, height in PLAUSIBLE:
                with self.subTest(sex=sex, age=age, height=height):
                    self.assertTrue(80.0 < mu(self.eq, sex, age, height, P.FEV1FVC) < 96.0)

    def test_volumes_rise_with_height(self):
        for sex in (M, F):
            for parameter in (P.FEV1, P.FVC, P.FEF25_75):
                with self.subTest(sex=sex, parameter=parameter.name):
                    self.assertLess(mu(self.eq, sex, 12, 130, parameter),
                                    mu(self.eq, sex, 12, 165, parameter))

    def test_predicted_ratio_falls_with_height(self):
        # Both sexes carry a negative height coefficient for FEV1/FVC.
        for sex in (M, F):
            with self.subTest(sex=sex):
                self.assertGreater(mu(self.eq, sex, 12, 130, P.FEV1FVC),
                                   mu(self.eq, sex, 12, 165, P.FEV1FVC))

    def test_lln_below_median_below_uln(self):
        for sex in (M, F):
            for parameter in P:
                with self.subTest(sex=sex, parameter=parameter.name):
                    lln = self.eq.lln(sex, 12, 150, parameter.value, 1.0)
                    uln = self.eq.uln(sex, 12, 150, parameter.value, 1.0)
                    median = mu(self.eq, sex, 12, 150, parameter)
                    self.assertLess(lln, median)
                    self.assertLess(median, uln)


class TestALQerem2021Metrics(unittest.TestCase):

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_zscore_of_the_median_is_zero(self):
        for sex in (M, F):
            for parameter in P:
                with self.subTest(sex=sex, parameter=parameter.name):
                    median = mu(self.eq, sex, 10, 140, parameter)
                    z = self.eq.zscore(sex, 10, 140, parameter.value, median)
                    self.assertAlmostEqual(z, 0.0, places=9)

    def test_zscore_of_the_lln_is_minus_1_645(self):
        for sex in (M, F):
            for parameter in P:
                with self.subTest(sex=sex, parameter=parameter.name):
                    lln = self.eq.lln(sex, 10, 140, parameter.value, 1.0)
                    z = self.eq.zscore(sex, 10, 140, parameter.value, lln)
                    self.assertAlmostEqual(z, -1.645, places=9)

    def test_zscore_of_the_uln_is_plus_1_645(self):
        for sex in (M, F):
            for parameter in P:
                with self.subTest(sex=sex, parameter=parameter.name):
                    uln = self.eq.uln(sex, 10, 140, parameter.value, 1.0)
                    z = self.eq.zscore(sex, 10, 140, parameter.value, uln)
                    self.assertAlmostEqual(z, 1.645, places=9)

    def test_percent_of_the_median_is_one_hundred(self):
        for sex in (M, F):
            for parameter in P:
                with self.subTest(sex=sex, parameter=parameter.name):
                    median = mu(self.eq, sex, 10, 140, parameter)
                    self.assertAlmostEqual(
                        self.eq.percent(sex, 10, 140, parameter.value, median), 100.0, places=2)

    def test_all_agrees_with_the_individual_metrics(self):
        pct, z, lln, uln = self.eq.all(M, 12, 150, P.FEV1.value, 2.5)
        self.assertAlmostEqual(pct, self.eq.percent(M, 12, 150, P.FEV1.value, 2.5), places=9)
        self.assertAlmostEqual(z, self.eq.zscore(M, 12, 150, P.FEV1.value, 2.5), places=9)
        self.assertAlmostEqual(lln, self.eq.lln(M, 12, 150, P.FEV1.value, 2.5), places=9)
        self.assertAlmostEqual(uln, self.eq.uln(M, 12, 150, P.FEV1.value, 2.5), places=9)

    def test_keyword_call_convention(self):
        positional = self.eq.zscore(M, 12, 150, P.FEV1.value, 2.5)
        keyword = self.eq.zscore(sex=M, age=12, height=150, parameter=P.FEV1.value, value=2.5)
        self.assertAlmostEqual(positional, keyword, places=9)


class TestALQerem2021Ranges(unittest.TestCase):

    def setUp(self):
        self.eq = ALQEREM_2021()

    def test_age_below_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.zscore(M, 5.0, 110, P.FEV1.value, 1.5)))

    def test_age_above_range_returns_na(self):
        self.assertTrue(pd.isna(self.eq.zscore(M, 18.5, 175, P.FEV1.value, 4.0)))

    def test_lms_returns_a_triplet_of_na_out_of_range(self):
        self.assertTrue(all(pd.isna(v) for v in self.eq.lms(M, 5.0, 110, P.FEV1.value, 1.5)))

    def test_closest_strategy_clamps_to_the_boundary(self):
        self.eq.set_strategy("closest")
        self.assertAlmostEqual(mu(self.eq, M, 20.0, 168, P.FEV1),
                               mu(self.eq, M, 17.75, 168, P.FEV1), places=9)
        self.assertAlmostEqual(mu(self.eq, M, 3.0, 116, P.FEV1),
                               mu(self.eq, M, 6.0, 116, P.FEV1), places=9)

    def test_age_is_rounded_to_the_nearest_quarter_year(self):
        # 12.30 and 12.20 both round to 12.25; 12.40 rounds to 12.50.
        self.assertAlmostEqual(mu(self.eq, M, 12.30, 150, P.FEV1),
                               mu(self.eq, M, 12.20, 150, P.FEV1), places=9)
        self.assertNotAlmostEqual(mu(self.eq, M, 12.30, 150, P.FEV1),
                                  mu(self.eq, M, 12.40, 150, P.FEV1), places=6)

    def test_rounding_may_not_push_a_valid_age_out_of_range(self):
        # 17.80 rounds to 17.75, the last knot, and must stay in range.
        self.assertFalse(pd.isna(mu(self.eq, M, 17.80, 168, P.FEV1)))

    def test_invalid_sex_returns_na(self):
        self.assertTrue(all(pd.isna(v) for v in self.eq.lms(2, 12, 150, P.FEV1.value, 2.5)))
        self.assertTrue(pd.isna(self.eq.zscore(2, 12, 150, P.FEV1.value, 2.5)))


class TestALQerem2021Compute(unittest.TestCase):
    """The vectorised DataFrame interface inherited from LMSReference."""

    def setUp(self):
        self.eq = ALQEREM_2021()
        self.df = pd.DataFrame({
            'sex': [s['sex'] for s in SUBJECTS],
            'age': [s['age'] for s in SUBJECTS],
            'height': [s['height'] for s in SUBJECTS],
            'FEV1': [s['fev1'] for s in SUBJECTS],
        })

    def test_compute_returns_one_column_per_metric(self):
        out = self.eq.compute(self.df, P.FEV1.value, value_col='FEV1')
        self.assertEqual(list(out.columns), ['percent', 'zscore', 'lln', 'uln'])
        self.assertEqual(len(out), len(SUBJECTS))

    def test_compute_zscore_matches_the_authors_values(self):
        out = self.eq.compute(self.df, P.FEV1.value, value_col='FEV1', metrics=('zscore',))
        for i, s in enumerate(SUBJECTS):
            with self.subTest(sex=s['sex'], age=s['age']):
                self.assertAlmostEqual(out['zscore'].iloc[i], s['z_fev1'], delta=1e-3)

    def test_compute_lln_needs_no_value_column(self):
        out = self.eq.compute(self.df, P.FVC.value, metrics=('lln',))
        self.assertEqual(len(out), len(SUBJECTS))
        self.assertTrue(out['lln'].notna().all())

    def test_compute_percent_without_value_column_raises(self):
        with self.assertRaises(ValueError):
            self.eq.compute(self.df, P.FEV1.value, metrics=('percent',))

    def test_compute_accepts_custom_column_names(self):
        df = self.df.rename(columns={'sex': 'gender', 'height': 'ht_cm'})
        out = self.eq.compute(df, P.FEV1.value, sex_col='gender', height_col='ht_cm',
                              value_col='FEV1', metrics=('zscore',))
        for i, s in enumerate(SUBJECTS):
            self.assertAlmostEqual(out['zscore'].iloc[i], s['z_fev1'], delta=1e-3)


if __name__ == '__main__':
    unittest.main()
