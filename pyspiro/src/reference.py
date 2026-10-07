from abc import ABC, abstractmethod
from enum import Enum
import inspect
import math

import numpy
import pandas
from pandas import NA


class Reference(ABC):
    """
    Abstract base class for all lung function reference equation implementations.

    Subclasses implement LMS-based (Box-Cox) or polynomial prediction equations
    for spirometry, lung volumes, diffusion capacity, or oscillometry.

    Out-of-range handling is controlled by set_strategy():
        "ignore"  (default) — returns pd.NA for out-of-range inputs.
        "closest"           — clamps to the nearest boundary value.

    Argument conventions
    --------------------
    sex        : 0 = female, 1 = male
    age        : years
    height     : cm
    ethnicity  : equation-specific integer code; omit or pass None for
                 race-neutral equations that do not stratify by ethnicity.
    parameter  : Parameters enum value (class-specific)
    value      : the measured value to evaluate
    """

    _strategy = "ignore"
    _silent = True

    def set_strategy(self, strategy: str):
        """Set the out-of-range handling strategy ('ignore' or 'closest')."""
        if strategy in ("ignore", "closest"):
            self._strategy = strategy
            return True
        return False

    def set_silence(self, silent: bool):
        """Suppress (True) or enable (False) out-of-range warning messages."""
        self._silent = silent

    def get_strategy(self):
        """Return the current out-of-range handling strategy."""
        return self._strategy

    @abstractmethod
    def percent(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the measured value as % of the predicted median."""
        pass

    @abstractmethod
    def zscore(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the z-score of the measured value relative to the reference distribution."""
        pass

    @abstractmethod
    def lms(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the (L, M, S) triplet for the given inputs."""
        pass

    @abstractmethod
    def lln(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the lower limit of normal (5th percentile)."""
        pass

    @abstractmethod
    def uln(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the upper limit of normal (95th percentile)."""
        pass

    def compute(self, df: pandas.DataFrame, parameter: int,
                sex_col: str = 'sex', age_col: str = 'age', height_col: str = 'height',
                value_col: str = None, ethnicity_col: str = None, weight_col: str = None,
                metrics: tuple = ('percent', 'zscore', 'lln', 'uln')) -> pandas.DataFrame:
        """
        Apply the reference equation to every row of a DataFrame.

        Parameters
        ----------
        df            : DataFrame with one patient per row.
        parameter     : Parameters enum value (or its integer value) to evaluate.
        sex_col       : column name for sex (0=female, 1=male).  Default 'sex'.
        age_col       : column name for age in years.            Default 'age'.
        height_col    : column name for height in cm.            Default 'height'.
        value_col     : column name for the measured value.
                        Required for 'percent' and 'zscore'; optional for 'lln'/'uln'.
        ethnicity_col : column name for ethnicity code.
                        Pass for equations that stratify by ethnicity (GLI_2012,
                        HANKINSON_1999). For equations that accept but ignore
                        ethnicity (KUSTER_2008), omitting this defaults to 0.
        weight_col    : column name for body weight in kg.
                        Required for SCHULZ_2013 lln/uln.
        metrics       : tuple of metrics to compute, any subset of
                        ('percent', 'zscore', 'lln', 'uln').  Default: all four.

        Returns
        -------
        DataFrame indexed like df with one column per requested metric.
        """
        def _explicit_params(metric_name):
            """Return the set of explicit (non-*args/**kwargs) parameter names."""
            try:
                sig = inspect.signature(getattr(self, metric_name))
                return frozenset(
                    n for n, p in sig.parameters.items()
                    if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD) and n != 'self'
                )
            except (TypeError, AttributeError, ValueError):
                return frozenset()

        sig_cache = {m: _explicit_params(m) for m in metrics}

        for metric, params in sig_cache.items():
            if 'weight' in params and weight_col is None:
                raise ValueError(
                    f"{type(self).__name__}.{metric}() requires a weight argument; "
                    "pass weight_col='<column_name>' to compute()."
                )
            if 'value' in params and value_col is None and metric in ('percent', 'zscore'):
                raise ValueError(
                    f"metric '{metric}' requires a measured value; "
                    "pass value_col='<column_name>' to compute()."
                )

        def _kw(row, params):
            kw = {
                'sex': int(row[sex_col]),
                'age': float(row[age_col]),
                'height': float(row[height_col]),
                'parameter': parameter,
            }
            if 'ethnicity' in params:
                # If no column supplied, default to 0 — equations that ignore ethnicity
                # (KUSTER_2008) work fine; those that use it (HANKINSON_1999) will raise
                # a clear ValueError from the equation itself.
                kw['ethnicity'] = int(row[ethnicity_col]) if ethnicity_col is not None else 0
            if 'weight' in params:
                kw['weight'] = float(row[weight_col])
            if 'value' in params:
                kw['value'] = float(row[value_col]) if value_col is not None else 0.0
            return kw

        result = {}
        for metric in metrics:
            method = getattr(self, metric)
            params = sig_cache[metric]
            result[metric] = df.apply(lambda r, m=method, p=params: m(**_kw(r, p)), axis=1)

        return pandas.DataFrame(result, index=df.index)

    def check_range(self, value: float, value_range: tuple):
        return value_range[0] <= value <= value_range[1]

    def check_tuple(self, value: float, allowed: tuple, value_type: str = "value"):
        for i in allowed:
            if value == i:
                return value
        if not self._silent:
            print("The given %s of %.2f is not fitting to the allow values %s" % (value_type, value, str(allowed)))
        return NA

    def validate_range(self, value: float, value_range: tuple, value_type: str = "value"):
        if not self.check_range(value, value_range):
            if not self._silent:
                print("The given %s of %.2f does not fit to the defined %s range %.2f-%.2f" % (value_type, value, value_type, value_range[0], value_range[1]))

            if self._strategy == "closest":
                old_value = value
                if value <= value_range[0]:
                    value = value_range[0]
                else:
                    value = value_range[1]
                print("Set %s to %.2f from %.2f" % (value_type, value, old_value))
            elif self._strategy == "ignore":
                value = NA

        return value

    class Sex(Enum):
        FEMALE = 0
        MALE = 1


class LMSReference(Reference):
    """
    Intermediate base for LMS (Box-Cox) reference equations.

    Provides percent, zscore, lln, uln, and all, all derived from lms().
    Subclasses only need to implement lms(); the derived metrics are
    computed automatically.

    Both positional and keyword call conventions are supported so that
    equations with and without an ethnicity argument work transparently:

        gli.percent(1, 40, 175, 1, GLI_2012.Parameters.FEV1, 3.0)  # positional
        gli.percent(sex=1, age=40, height=175, parameter=1, value=3.0)  # keyword
    """

    def percent(self, *args, **kwargs):
        """Return % of predicted median."""
        l, m, s = self.lms(*args, **kwargs)
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA
        value = kwargs['value'] if 'value' in kwargs else args[-1]
        return round((value / m) * 100, 2)

    def zscore(self, *args, **kwargs):
        """Return z-score."""
        l, m, s = self.lms(*args, **kwargs)
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA
        value = kwargs['value'] if 'value' in kwargs else args[-1]
        return (((value / m) ** l) - 1) / (l * s)

    def lln(self, *args, **kwargs):
        """Return lower limit of normal (5th percentile)."""
        l, m, s = self.lms(*args, **kwargs)
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA
        return numpy.exp(numpy.log(1 - 1.645 * l * s) / l + numpy.log(m))

    def uln(self, *args, **kwargs):
        """Return upper limit of normal (95th percentile)."""
        l, m, s = self.lms(*args, **kwargs)
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA
        return numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m))

    def all(self, *args, **kwargs):
        """Return (percent, zscore, lln, uln) in a single call."""
        l, m, s = self.lms(*args, **kwargs)
        if l is pandas.NA or m is pandas.NA or s is pandas.NA:
            return pandas.NA, pandas.NA, pandas.NA, pandas.NA
        value = kwargs['value'] if 'value' in kwargs else args[-1]
        return (
            round((value / m) * 100, 2),
            (((value / m) ** l) - 1) / (l * s),
            numpy.exp(numpy.log(1 - 1.645 * l * s) / l + numpy.log(m)),
            numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m)),
        )

    def compute(self, df: pandas.DataFrame, parameter: int,
                sex_col: str = 'sex', age_col: str = 'age', height_col: str = 'height',
                value_col: str = None, ethnicity_col: str = None, weight_col: str = None,
                metrics: tuple = ('percent', 'zscore', 'lln', 'uln')) -> pandas.DataFrame:
        """
        Apply the reference equation to every row of a DataFrame.

        Parameters
        ----------
        df            : DataFrame with one patient per row.
        parameter     : Parameters enum value (or its integer value) to evaluate.
        sex_col       : column name for sex (0=female, 1=male).  Default 'sex'.
        age_col       : column name for age in years.            Default 'age'.
        height_col    : column name for height in cm.            Default 'height'.
        value_col     : column name for the measured value.
                        Required for 'percent' and 'zscore'; optional for 'lln'/'uln'.
        ethnicity_col : column name for ethnicity code.
                        Required when the equation's lms() includes an ethnicity
                        argument (e.g. GLI_2012); ignored otherwise.
        weight_col    : accepted for API consistency with non-LMS equations; ignored.
        metrics       : tuple of metrics to compute, any subset of
                        ('percent', 'zscore', 'lln', 'uln').  Default: all four.

        Returns
        -------
        DataFrame indexed like df with one column per requested metric.

        Examples
        --------
        >>> gli = GLI_2012()
        >>> results = gli.compute(df, GLI_2012.Parameters.FEV1,
        ...                       value_col='FEV1', ethnicity_col='ethnicity')
        >>> bow = BOWERMAN_2022()
        >>> results = bow.compute(df, BOWERMAN_2022.Parameters.FVC, value_col='FVC')
        >>> # Custom column names — e.g. 'gender' instead of 'sex':
        >>> results = bow.compute(df, BOWERMAN_2022.Parameters.FVC,
        ...                       sex_col='gender', age_col='age_years',
        ...                       height_col='ht_cm', value_col='fvc_measured')
        """
        lms_params = set(inspect.signature(self.lms).parameters)
        needs_ethnicity = 'ethnicity' in lms_params

        if needs_ethnicity and ethnicity_col is None:
            raise ValueError(
                f"{type(self).__name__}.lms requires an ethnicity argument; "
                "pass ethnicity_col='<column_name>' to compute()."
            )
        for metric in metrics:
            if metric in ('percent', 'zscore') and value_col is None:
                raise ValueError(
                    f"metric '{metric}' requires a measured value; "
                    "pass value_col='<column_name>' to compute()."
                )

        def _kw(row):
            kw = {
                'sex': int(row[sex_col]),
                'age': float(row[age_col]),
                'height': float(row[height_col]),
                'parameter': parameter,
                'value': float(row[value_col]) if value_col is not None else 0.0,
            }
            if needs_ethnicity:
                kw['ethnicity'] = int(row[ethnicity_col])
            return kw

        result = {}
        for metric in metrics:
            method = getattr(self, metric)
            result[metric] = df.apply(lambda r, m=method: m(**_kw(r)), axis=1)

        return pandas.DataFrame(result, index=df.index)


class SplineReference(LMSReference):
    """
    Shared CSV loader and spline accessor for GLI-family references.

    Subclasses declare two class-level strings:
        _splines_csv : filename of the age-indexed spline table in pyspiro.data
        _coeffs_csv  : filename of the var-indexed coefficient table in pyspiro.data

    The constructor loads both CSVs and stores them as self._lookup and
    self._coefficients. The _get_splines() helper yields (Sspline, Mspline,
    Lspline) from the table row of a given age; _age_and_splines() validates
    the age and linearly interpolates the splines between the rows, as
    prescribed for the GLI equations (Quanjer 2012 online supplement,
    section 4; the GLI-2017 TLCO calculator does the same).

    Subclasses only need to implement lms(); everything else is inherited.
    """

    _splines_csv: str
    _coeffs_csv: str

    _AGE_STEP = 0.25

    def __init__(self):
        import importlib.resources
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / self._splines_csv).open('rb') as f:
            lookup = pandas.read_csv(f, delimiter=";").set_index("age")
        with (pkg / self._coeffs_csv).open('rb') as f:
            splines = pandas.read_csv(f, delimiter=";").set_index("var")
        self._age_range = (min(lookup.index), max(lookup.index))
        self._lookup = lookup
        self._coefficients = splines
        # Some tables end earlier for some parameters (GLI_2012 FEF25-75/FEF75: 90 y)
        self._spline_age_ranges = {
            column[:-len("_Mspline")]: (min(ages), max(ages))
            for column in lookup.columns if column.endswith("_Mspline")
            for ages in [lookup[column].dropna().index]
        }

    def _spline_prefix(self, sex: int, parameter: int) -> str:
        return "%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())

    def _get_splines(self, sex: int, age: float, parameter: int):
        """Yield (Sspline, Mspline, Lspline) from the age-indexed lookup table."""
        prefix = self._spline_prefix(sex, parameter)
        for i in ("Sspline", "Mspline", "Lspline"):
            yield self._lookup["%s_%s" % (prefix, i)].loc[age]

    def _interpolated_splines(self, sex: int, age: float, parameter: int, age_range: tuple) -> tuple:
        """Return (Sspline, Mspline, Lspline) linearly interpolated between the table rows around age."""
        lower = math.floor(age / self._AGE_STEP) * self._AGE_STEP
        weight = (age - lower) / self._AGE_STEP
        lower_splines = tuple(self._get_splines(sex, lower, parameter))
        if weight == 0:
            return lower_splines
        upper = min(lower + self._AGE_STEP, age_range[1])
        upper_splines = tuple(self._get_splines(sex, upper, parameter))
        return tuple((1 - weight) * x + weight * y for x, y in zip(lower_splines, upper_splines))

    def _age_and_splines(self, sex: int, age: float, parameter: int) -> tuple:
        """
        Validate age against the parameter's look-up table and return
        (age, Sspline, Mspline, Lspline). The age is kept exact (or clamped by
        the 'closest' strategy) for the closed-form terms of the equation.
        Returns (NA, NA, NA, NA) when the age is out of range.
        """
        age_range = self._spline_age_ranges[self._spline_prefix(sex, parameter)]
        age = self.validate_range(age, age_range, "age")
        if age is NA:
            return NA, NA, NA, NA
        return (age,) + self._interpolated_splines(sex, age, parameter, age_range)


class Classifier(ABC):
    """Abstract base class for spirometry severity classifiers (e.g. GOLD, STAR)."""

    def get_order(self):
        """Return the ordered list of severity stages."""
        return self._order

    def set_order(self, order: list):
        _order = order

    @abstractmethod
    def classify(self, **kwargs):
        """Classify the patient into a severity stage and return the stage label."""
        pass
