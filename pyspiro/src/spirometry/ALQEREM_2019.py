from ..reference import RegressionReference, RegressionResult, _metric_column
from enum import Enum
import importlib.resources
import math
import numpy
import pandas


class ALQEREM_2019(RegressionReference):
    """
    Middle Eastern (Jordanian) spirometry reference equations (Al Qerem et al. 2019).

    GAMLSS reference equations derived from 1,949 healthy non-smoking Jordanian
    adults (888 males, 1,061 females) and validated in a further 300 subjects.
    Each parameter was fitted with the best of several candidate models, so the
    distribution family differs between parameters:

        NO   (Normal)  — parameters (mu, sigma); sigma is an absolute SD.
        BCCG (LMS)     — parameters (mu = median, sigma = coefficient of
                         variation, nu = Box-Cox skewness power).

    Equation form (height h in cm, age a in years):
        eta_mu = mu_int + mu_lnht*ln(h) + mu_lnage*ln(a) [+ MSpline(a)]
        mu     = exp(eta_mu)   if the mean uses a log link
               = eta_mu        if the mean uses an identity link
        sigma  = exp(sg_int + sg_lnht*ln(h) + sg_lnage*ln(a) [+ SSpline(a)])
        nu     = nu_int + nu_lnage*ln(a)     (BCCG only)

    Metrics:
        Normal (NO):
            zscore = (value - mu) / sigma
            lln    = mu - 1.645*sigma ;  uln = mu + 1.645*sigma
        BCCG:
            zscore = ((value/mu)**nu - 1) / (nu*sigma)          (nu != 0)
            lln/uln = mu * (1 + nu*sigma*z)**(1/nu),  z = -/+1.645
        percent = value / mu * 100   (mu is the mean/median)

    The age-spline lookup (supplementary Tables 1-12) is sampled at 0.25-year
    steps; input age is rounded to the nearest 0.25 year for lookup. The
    coefficients in log/identity terms use the exact (unrounded) age. The
    skewness (nu) spline was zero throughout the published tables and is omitted.

    Notes:
        * FEV1FVC is expressed as a percentage (0-100), matching the publication
          (e.g. pass 85.0, not 0.85).
        * FVC in males (Model 6) and FEV1/FVC in both sexes (Model 1) were fitted
          without meaningful age-splines, so no spline is applied to them.
        * Where the BCCG skewness constant was not tabulated (Models 2 and 6, the
          "vector starts at 1" fits: male FVC, female FEV1), nu = 1.0 is used,
          consistent with every other Model 2/6 parameter for which nu = 1.00 was
          reported.

    Variables: sex (0=female, 1=male), age (years; 18-83 males, 18-78 females),
    height (cm, 140-200). No ethnicity stratification.

    The paper reports reference equations and summary statistics (Table 2) but no
    per-subject worked examples; tests cross-check predicted means against Table 2.

    Coefficients: alqerem_2019_coefficients.csv (Tables 4 and 5).
    Age-splines:  alqerem_2019_splines.csv (supplementary Tables 1-12).

    Citation:
        Al Qerem W, Hammad AM, Gassar ES, Al-Qirim RA, Ling J. Spirometry
        reference equations for an adult middle eastern population. Expert Rev
        Respir Med. 2019;13(6):489-497. doi: 10.1080/17476348.2019.1601560.
        PMID: 30935243.
    """

    class Parameters(Enum):
        FEV1    = 1
        FVC     = 2
        FEV1FVC = 3   # expressed as a percentage (0-100)
        FEF75   = 4
        FEF2575 = 5
        FEF25   = 6
        FEF50   = 7

    _AGE_RANGE_MALE   = (18, 83)
    _AGE_RANGE_FEMALE = (18, 78)
    _HEIGHT_RANGE     = (140, 200)

    def __init__(self):
        self._coefficients, self._splines = self._load_data()
        self._height_range = self._HEIGHT_RANGE

    def _load_data(self):
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / 'alqerem_2019_coefficients.csv').open('rb') as f:
            coeffs = pandas.read_csv(f, delimiter=';').set_index(['sex', 'parameter'])
        with (pkg / 'alqerem_2019_splines.csv').open('rb') as f:
            spl = pandas.read_csv(f, delimiter=';')
        splines = {
            (int(r.sex), r.parameter, round(float(r.age), 2)): (float(r.mspline), float(r.sspline))
            for r in spl.itertuples(index=False)
        }
        return coeffs, splines

    def _age_range(self, sex: int) -> tuple:
        return self._AGE_RANGE_MALE if sex == self.Sex.MALE.value else self._AGE_RANGE_FEMALE

    @staticmethod
    def _spline_key(age: float) -> float:
        return round(round(age * 4) / 4, 2)

    def _spline(self, sex: int, param_name: str, age: float):
        return self._splines.get((int(sex), param_name, self._spline_key(age)), (0.0, 0.0))

    _ARRAY_REGRESSION = True

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        """mu as the predicted value, with sigma, nu (BCCG only) and the distribution."""
        age, na = self._validated(age, self._age_range(sex), 'age')
        height, na = self._validated(height, self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()

        param_name = self.Parameters(parameter).name
        c = self._row((int(sex), param_name), required=True)
        if not isinstance(age, numpy.ndarray):
            exp = math.exp
            lnht, lnage = math.log(float(height)), math.log(float(age))
            mspline, sspline = self._spline(sex, param_name, float(age))
        else:
            exp = numpy.exp
            lnht, lnage = numpy.log(height), numpy.log(age)
            keys = numpy.round(numpy.round(age * 4) / 4, 2).tolist()     # as _spline_key()
            splines = [self._splines.get((int(sex), param_name, key), (0.0, 0.0)) for key in keys]
            mspline = numpy.array([m for m, _ in splines])
            sspline = numpy.array([s for _, s in splines])
        eta_mu = (float(c['mu_int']) + float(c['mu_lnht']) * lnht
                  + float(c['mu_lnage']) * lnage
                  + (mspline if int(c['mu_spline']) else 0.0))
        mu = exp(eta_mu) if c['mu_link'] == 'log' else eta_mu
        sigma = exp(float(c['sg_int']) + float(c['sg_lnht']) * lnht
                    + float(c['sg_lnage']) * lnage
                    + (sspline if int(c['sg_spline']) else 0.0))
        if c['dist'] == 'BCCG':
            nu = float(c['nu_int']) + float(c['nu_lnage']) * lnage
        else:
            nu = None
        return RegressionResult(mu, na=na, sigma=sigma, nu=nu, normal=c['dist'] == 'NO')

    def _params(self, sex: int, age: float, height: float, parameter: int):
        """Return (dist, mu, sigma, nu) or (None, pandas.NA, pandas.NA, pandas.NA)."""
        r = self._regression(sex, age, height, None, None, parameter)
        if r.na:
            return None, pandas.NA, pandas.NA, pandas.NA
        return ('NO' if r.normal else 'BCCG'), r.pred, r.sigma, r.nu

    def lms(self, sex, age, height, parameter=None, value=None):
        """Return (L, M, S) = (nu, mu, sigma) for BCCG parameters.

        Returns (pandas.NA, pandas.NA, pandas.NA) for Normal (NO) parameters,
        which are not LMS models.
        """
        dist, mu, sigma, nu = self._params(sex, age, height, parameter)
        if mu is pandas.NA or dist == 'NO':
            return pandas.NA, pandas.NA, pandas.NA
        return nu, mu, sigma

    def percent(self, sex, age, height, parameter=None, value=None):
        """Return measured value as % of the predicted mean/median."""
        _, mu, _, _ = self._params(sex, age, height, parameter)
        return pandas.NA if mu is pandas.NA else round(value / mu * 100, 2)

    def zscore(self, sex, age, height, parameter=None, value=None):
        """Return z-score of the measured value under the fitted distribution."""
        dist, mu, sigma, nu = self._params(sex, age, height, parameter)
        if mu is pandas.NA:
            return pandas.NA
        if dist == 'NO':
            return (value - mu) / sigma
        if abs(nu) < 1e-8:
            return math.log(value / mu) / sigma
        return ((value / mu) ** nu - 1) / (nu * sigma)

    def _centile(self, sex, age, height, parameter, z):
        dist, mu, sigma, nu = self._params(sex, age, height, parameter)
        if mu is pandas.NA:
            return pandas.NA
        if dist == 'NO':
            return mu + z * sigma
        if abs(nu) < 1e-8:
            return mu * math.exp(z * sigma)
        base = 1 + nu * sigma * z
        return pandas.NA if base <= 0 else mu * base ** (1 / nu)

    def lln(self, sex, age, height, parameter=None):
        """Return lower limit of normal (5th percentile, z = -1.645)."""
        return self._centile(sex, age, height, parameter, -1.645)

    def uln(self, sex, age, height, parameter=None):
        """Return upper limit of normal (95th percentile, z = +1.645)."""
        return self._centile(sex, age, height, parameter, 1.645)

    def predicted(self, sex, age, height, parameter=None):
        """Return the predicted mean/median for the given inputs."""
        _, mu, _, _ = self._params(sex, age, height, parameter)
        return mu

    def _metric_from_arrays(self, metric, merged, value, index):
        if metric not in ('zscore', 'lln', 'uln'):
            return super()._metric_from_arrays(metric, merged, value, index)
        if merged.na.all():
            return _metric_column(numpy.full(merged.n, numpy.nan), merged.na, index)
        r = merged.result()
        na = merged.na.copy()
        normal = numpy.asarray(r.normal, dtype=bool) & ~na
        bccg = ~normal & ~na
        mu, sigma = r.pred, r.sigma
        nu = getattr(r, 'nu', None)       # absent when no row has a BCCG distribution
        if nu is None:
            nu = numpy.full(merged.n, numpy.nan)
        log_normal = bccg & (numpy.abs(nu) < 1e-8)
        power = bccg & ~log_normal
        values = numpy.full(merged.n, numpy.nan)
        with numpy.errstate(all="ignore"):
            if metric == 'zscore':
                ratio = value / mu
                if (ratio[bccg] <= 0).any():
                    return None       # math.log() raises, negative ** nu is complex: row-wise path
                values[normal] = ((value - mu) / sigma)[normal]
                values[log_normal] = (numpy.log(ratio) / sigma)[log_normal]
                values[power] = (((ratio) ** nu - 1) / (nu * sigma))[power]
            else:
                z = -1.645 if metric == 'lln' else 1.645
                values[normal] = (mu + z * sigma)[normal]
                values[log_normal] = (mu * numpy.exp(z * sigma))[log_normal]
                base = 1 + nu * sigma * z
                na |= power & (base <= 0)
                ok = power & (base > 0)
                values[ok] = (mu * base ** (1 / nu))[ok]
        return _metric_column(values, na, index)
