from abc import ABC, abstractmethod
from enum import Enum
import inspect
import math

import numpy
import pandas
from pandas import NA


def _int_array(series: pandas.Series) -> numpy.ndarray:
    """Convert a column like int() does per value (truncation; NaN raises ValueError)."""
    values = series.to_numpy()
    if values.dtype.kind in "iub":
        return values.astype(numpy.int64)
    if values.dtype.kind == "f":
        if numpy.isnan(values).any():
            raise ValueError("cannot convert float NaN to integer")
        if numpy.isinf(values).any():
            raise OverflowError("cannot convert float infinity to integer")
        return values.astype(numpy.int64)
    return numpy.array([int(v) for v in values], dtype=numpy.int64)


def _float_array(series: pandas.Series) -> numpy.ndarray:
    """Convert a column like float() does per value."""
    values = series.to_numpy()
    if values.dtype.kind in "iubf":
        return values.astype(float)
    return numpy.array([float(v) for v in values], dtype=float)


class _ComputeColumns:
    """
    Input columns of compute(), converted once and only when needed: as
    NumPy arrays (``*_array``) for the vectorised path and as lists of Python
    scalars for the row-wise path, matching the int()/float() conversion that
    compute() has always applied per row.
    """

    def __init__(self, df, sex_col, age_col, height_col, value_col, ethnicity_col, weight_col):
        self._df = df
        self._cols = {'sex': sex_col, 'age': age_col, 'height': height_col,
                      'value': value_col, 'ethnicity': ethnicity_col, 'weight': weight_col}
        self._cache = {}

    def _array(self, name):
        if name not in self._cache:
            convert = _int_array if name in ('sex', 'ethnicity') else _float_array
            self._cache[name] = convert(self._df[self._cols[name]])
        return self._cache[name]

    def _list(self, name):
        key = name + '_list'
        if key not in self._cache:
            self._cache[key] = self._array(name).tolist()
        return self._cache[key]

    sex = property(lambda self: self._list('sex'))
    age = property(lambda self: self._list('age'))
    height = property(lambda self: self._list('height'))
    weight = property(lambda self: self._list('weight'))
    weight_array = property(lambda self: self._array('weight'))
    sex_array = property(lambda self: self._array('sex'))
    age_array = property(lambda self: self._array('age'))
    height_array = property(lambda self: self._array('height'))

    def value_or(self, default):
        return self._list('value') if self._cols['value'] is not None else default

    def value_array_or(self, default):
        if self._cols['value'] is not None:
            return self._array('value')
        return numpy.full(len(self._df), default, dtype=float)

    def ethnicity_or(self, default):
        return self._list('ethnicity') if self._cols['ethnicity'] is not None else default

    def ethnicity_array(self):
        return self._array('ethnicity')


def _metric_column(values: numpy.ndarray, na: numpy.ndarray, index, element=float) -> pandas.Series:
    """
    Series as the row-wise compute() builds it: float64 when no row is NA,
    otherwise object dtype with pd.NA in the NA rows and the other rows of
    the type the scalar method returns (element: float or numpy.float64).
    """
    if not na.any():
        return pandas.Series(values, index=index)
    if element is float:
        column = values.astype(object)
    else:
        column = numpy.empty(len(values), dtype=object)
        column[:] = list(values)        # iterating an array yields numpy.float64
    column[na] = NA
    return pandas.Series(column, index=index, dtype=object)


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

        LMSReference and RegressionReference equations evaluate whole columns
        at once (vectorised); the result equals calling the scalar methods row
        by row (same values, NA rows, dtypes and exceptions; out-of-range
        messages are printed once per row rather than once per row and metric).
        This base implementation calls the scalar methods once per row.

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
        sig_cache = {m: self._metric_params(m) for m in metrics}
        self._check_compute_arguments(sig_cache, value_col, weight_col)

        columns = _ComputeColumns(df, sex_col, age_col, height_col, value_col, ethnicity_col, weight_col)

        result = {}
        for metric in metrics:
            params = sig_cache[metric]
            # If no ethnicity column is supplied, default to 0 — equations that ignore
            # ethnicity (KUSTER_2008) work fine; those that use it (HANKINSON_1999) will
            # raise a clear ValueError from the equation itself.
            kwargs = {
                'sex': columns.sex,
                'age': columns.age,
                'height': columns.height,
                'parameter': parameter,
            }
            if 'ethnicity' in params:
                kwargs['ethnicity'] = columns.ethnicity_or(0)
            if 'weight' in params:
                kwargs['weight'] = columns.weight
            if 'value' in params:
                kwargs['value'] = columns.value_or(0.0)
            result[metric] = self._rowwise(getattr(self, metric), kwargs, df.index)

        return pandas.DataFrame(result, index=df.index)

    def _metric_params(self, metric_name) -> frozenset:
        """Return the set of explicit (non-*args/**kwargs) parameter names of a metric method."""
        try:
            sig = inspect.signature(getattr(self, metric_name))
            return frozenset(
                n for n, p in sig.parameters.items()
                if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD) and n != 'self'
            )
        except (TypeError, AttributeError, ValueError):
            return frozenset()

    def _check_compute_arguments(self, sig_cache: dict, value_col, weight_col):
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

    @staticmethod
    def _rowwise(method, kwargs: dict, index) -> pandas.Series:
        """
        Call a scalar method once per row. kwargs maps argument names to
        per-row lists (Python scalars, as the scalar methods expect) or to a
        constant (the parameter).
        """
        names = list(kwargs)
        per_row = [kwargs[n] if isinstance(kwargs[n], list) else [kwargs[n]] * len(index) for n in names]
        values = [method(**dict(zip(names, row))) for row in zip(*per_row)]
        return pandas.Series(values, index=index, dtype=None if values else float)

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

    def _validate_range_array(self, values, value_range: tuple, value_type: str = "value") -> tuple:
        """
        Array twin of validate_range(). Returns (values, na): the values,
        clamped to the range by the 'closest' strategy, and a boolean mask of
        the entries that validate_range() would turn into NA ('ignore').
        """
        values = numpy.array(values, dtype=float)
        with numpy.errstate(invalid="ignore"):
            outside = ~((value_range[0] <= values) & (values <= value_range[1]))
        na = numpy.zeros(values.shape, dtype=bool)
        if not outside.any():
            return values, na
        for value in values[outside]:
            # validate_range() also prints NaN as out of range; 'closest' then sets it to the upper limit
            if not self._silent:
                print("The given %s of %.2f does not fit to the defined %s range %.2f-%.2f" % (value_type, value, value_type, value_range[0], value_range[1]))
            if self._strategy == "closest":
                print("Set %s to %.2f from %.2f" % (value_type, value_range[0] if value <= value_range[0] else value_range[1], value))
        if self._strategy == "closest":
            values[outside] = numpy.where(values[outside] <= value_range[0], value_range[0], value_range[1])
        elif self._strategy == "ignore":
            na = outside
        return values, na

    class Sex(Enum):
        FEMALE = 0
        MALE = 1


class LMSReference(Reference):
    """
    Intermediate base for LMS (Box-Cox) reference equations.

    Provides percent, zscore, lln, uln, and all, all derived from lms().
    Subclasses only need to implement lms(); the derived metrics are
    computed automatically. compute() calls lms() per row unless the
    subclass also provides the array twin _sex_lms_arrays() (see below).

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

        columns = _ComputeColumns(df, sex_col, age_col, height_col, value_col, ethnicity_col, weight_col)

        if self._lms_vectorised(metrics):
            return self._compute_vectorised(columns, parameter, metrics, needs_ethnicity, df.index)

        kwargs = {
            'sex': columns.sex,
            'age': columns.age,
            'height': columns.height,
            'parameter': parameter,
            'value': columns.value_or(0.0),
        }
        if needs_ethnicity:
            kwargs['ethnicity'] = columns.ethnicity_or(None)

        result = {}
        for metric in metrics:
            result[metric] = self._rowwise(getattr(self, metric), kwargs, df.index)

        return pandas.DataFrame(result, index=df.index)

    # ── Vectorised compute() ────────────────────────────────────────────────
    #
    # A subclass opts in by implementing _sex_lms_arrays() (or _lms_arrays())
    # and setting _ARRAY_LMS = True in the class body that defines lms(). The
    # flag is read from that class only, so a subclass that overrides lms()
    # without providing the array twin keeps the row-wise path.

    _ARRAY_LMS = False

    def _lms_vectorised(self, metrics) -> bool:
        """True if compute() may use _lms_arrays() instead of calling lms() per row."""
        owner = next(k for k in type(self).__mro__ if 'lms' in vars(k))
        if not vars(owner).get('_ARRAY_LMS', False):
            return False
        return all(getattr(type(self), m, None) is getattr(LMSReference, m) for m in metrics)

    def _compute_vectorised(self, columns, parameter, metrics, needs_ethnicity, index) -> pandas.DataFrame:
        ethnicity = columns.ethnicity_array() if needs_ethnicity else None
        l, m, s, na = self._lms_arrays(columns.sex_array, columns.age_array, columns.height_array,
                                       ethnicity, parameter)
        value = columns.value_array_or(0.0)
        result = {}
        for metric in metrics:
            with numpy.errstate(all="ignore"):
                values = self._metric_arrays(metric, l, m, s, value, na)
            if values is None:
                kwargs = {'sex': columns.sex, 'age': columns.age, 'height': columns.height,
                          'parameter': parameter, 'value': columns.value_or(0.0)}
                if needs_ethnicity:
                    kwargs['ethnicity'] = columns.ethnicity_or(None)
                result[metric] = self._rowwise(getattr(self, metric), kwargs, index)
            else:
                result[metric] = _metric_column(values, na, index, self._metric_element_type(metric))
        return pandas.DataFrame(result, index=index)

    def _metric_element_type(self, metric):
        """Type of the scalar metric values (M is a numpy.float64, so are the metrics)."""
        return numpy.float64

    def _metric_arrays(self, metric, l, m, s, value, na):
        """
        percent/zscore/lln/uln on arrays, with the expressions of the scalar
        methods; None hands the metric back to the row-wise path.
        """
        if metric == 'percent':
            # numpy rounding, as round() applies to the numpy.float64 that the scalar path computes
            return numpy.round((value / m) * 100, 2)
        if metric == 'zscore':
            return (((value / m) ** l) - 1) / (l * s)
        if metric == 'lln':
            return numpy.exp(numpy.log(1 - 1.645 * l * s) / l + numpy.log(m))
        if metric == 'uln':
            return numpy.exp(numpy.log(1 + 1.645 * l * s) / l + numpy.log(m))
        raise ValueError("unknown metric %r" % (metric,))

    def _lms_arrays(self, sex, age, height, ethnicity, parameter) -> tuple:
        """
        Array twin of lms() for whole columns: returns (L, M, S, na), where na
        marks the rows for which lms() returns NA. Rows are grouped by sex and
        passed to _sex_lms_arrays().
        """
        n = len(age)
        l, m, s = (numpy.full(n, numpy.nan) for _ in range(3))
        na = numpy.zeros(n, dtype=bool)
        for sex_value in numpy.unique(sex):
            rows = sex == sex_value
            group = self._sex_lms_arrays(int(sex_value), age[rows], height[rows],
                                         None if ethnicity is None else ethnicity[rows], parameter)
            l[rows], m[rows], s[rows], na[rows] = group
        return l, m, s, na

    def _sex_lms_arrays(self, sex: int, age, height, ethnicity, parameter) -> tuple:
        """(L, M, S, na) for rows of one sex; see _lms_arrays()."""
        raise NotImplementedError


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

    Subclasses implement the equation once, in _lms_equation(), which must
    work on scalars and on NumPy arrays alike; lms() delegates to
    _spline_lms(), and compute() evaluates whole columns through
    _sex_lms_arrays() (set _ARRAY_LMS = True next to lms()).
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

    def _spline_rows(self, prefix: str, ages) -> tuple:
        """(Sspline, Mspline, Lspline) arrays from the table rows at the given ages (NaN where a row is missing)."""
        positions = self._lookup.index.get_indexer(ages)
        missing = positions < 0
        splines = []
        for name in ("Sspline", "Mspline", "Lspline"):
            values = self._lookup["%s_%s" % (prefix, name)].to_numpy(dtype=float)[positions]
            values[missing] = numpy.nan
            splines.append(values)
        return tuple(splines)

    def _interpolated_splines_array(self, prefix: str, age, age_range: tuple) -> tuple:
        """Array twin of _interpolated_splines()."""
        lower = numpy.floor(age / self._AGE_STEP) * self._AGE_STEP
        weight = (age - lower) / self._AGE_STEP
        upper = numpy.minimum(lower + self._AGE_STEP, age_range[1])
        lower_splines = self._spline_rows(prefix, lower)
        upper_splines = self._spline_rows(prefix, upper)
        return tuple(numpy.where(weight == 0, x, (1 - weight) * x + weight * y)
                     for x, y in zip(lower_splines, upper_splines))

    def _age_and_splines_array(self, sex: int, age, parameter) -> tuple:
        """
        Array twin of _age_and_splines() for rows of one sex: returns
        (age, na, Sspline, Mspline, Lspline), na marking out-of-range rows.
        """
        prefix = self._spline_prefix(sex, parameter)
        age_range = self._spline_age_ranges[prefix]
        age, na = self._validate_range_array(age, age_range, "age")
        age = numpy.where(na, age_range[0], age)    # placeholder for NA rows, masked later
        return (age, na) + self._interpolated_splines_array(prefix, age, age_range)

    def _lms_equation(self, c, parameter, age, height, ethnicity, sspline, mspline, lspline) -> tuple:
        """
        The (L, M, S) equation with the coefficients c of one sex and
        parameter. Must accept scalars and NumPy arrays alike.
        """
        raise NotImplementedError

    def _spline_lms(self, sex: int, age: float, height: float, ethnicity, parameter) -> tuple:
        """Scalar lms(): validated age, interpolated splines, then _lms_equation()."""
        age, sspline, mspline, lspline = self._age_and_splines(sex, age, parameter)
        if age is NA:
            return NA, NA, NA
        c = self._coefficients[self._spline_prefix(sex, parameter)]
        return self._lms_equation(c, parameter, age, height, ethnicity, sspline, mspline, lspline)

    def _sex_lms_arrays(self, sex: int, age, height, ethnicity, parameter) -> tuple:
        age, na, sspline, mspline, lspline = self._age_and_splines_array(sex, age, parameter)
        c = self._coefficients[self._spline_prefix(sex, parameter)]
        with numpy.errstate(all="ignore"):
            l, m, s = self._lms_equation(c, parameter, age, height, ethnicity, sspline, mspline, lspline)
        return l, m, s, na


class IntegerAgeLMSReference(LMSReference):
    """
    LMS equations whose spline tables have one row per whole year of age
    (rspiro "agebound" tables: columns agebound, Lspline, Mspline, Sspline,
    gender (1 = male, 2 = female), f (parameter name)). The age is floored to
    the whole year for the spline look-up; the closed-form terms use the
    exact age. Ages without a table row return NA.

        L = q0 + q1*ln(Age) + Lspline   (Lspline where tabulated)
        M = exp(a0 + a1*ln(Ht) + a2*ln(Age) + Mspline)
        S = exp(p0 + p1*ln(Age) + Sspline)

    Subclasses declare _splines_csv, _coeffs_csv and _AGE_RANGE.
    """

    _splines_csv: str
    _coeffs_csv: str
    _AGE_RANGE: tuple

    _ARRAY_LMS = True

    def __init__(self):
        import importlib.resources
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / self._splines_csv).open('rb') as f:
            raw = pandas.read_csv(f, index_col=0)
        # Pre-index by (parameter_name, csv_gender) for O(1) age lookup
        self._spline_tables = {
            (name, int(gender)): group.set_index('agebound')
            for (name, gender), group in raw.groupby(['f', 'gender'])
        }
        with (pkg / self._coeffs_csv).open('rb') as f:
            self._coefficients = pandas.read_csv(f, delimiter=";").set_index("var")
        self._age_range = self._AGE_RANGE

    def _sex_to_gender(self, sex: int) -> int:
        """Map Sex enum value (0=female, 1=male) to the table's gender code (1=male, 2=female)."""
        return 1 if sex == self.Sex.MALE.value else 2

    def _spline_table(self, sex: int, parameter):
        return self._spline_tables.get((self.Parameters(parameter).name, self._sex_to_gender(sex)))

    def _splines_at(self, sex: int, age_int: int, parameter: int) -> tuple:
        """(Sspline, Mspline, Lspline) of the whole-year row; NA if there is none."""
        table = self._spline_table(sex, parameter)
        if table is None or age_int not in table.index:
            return NA, NA, NA
        row = table.loc[age_int]
        return float(row['Sspline']), float(row['Mspline']), row['Lspline']

    def _equation(self, c, age, height, sspline, mspline, lspline) -> tuple:
        """The (L, M, S) equation; accepts scalars and NumPy arrays alike."""
        l = float(c.loc["q0"]) + float(c.loc["q1"]) * numpy.log(age)
        l = numpy.where(numpy.isnan(lspline), l, l + lspline) if numpy.ndim(l) else (
            l if pandas.isna(lspline) else l + float(lspline))
        m = numpy.exp(float(c.loc["a0"])
                      + float(c.loc["a1"]) * numpy.log(height)
                      + float(c.loc["a2"]) * numpy.log(age)
                      + mspline)
        s = numpy.exp(float(c.loc["p0"])
                      + float(c.loc["p1"]) * numpy.log(age)
                      + sspline)
        return l, m, s

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float = None) -> tuple:
        """Return the (L, M, S) triplet for the given inputs."""
        age = self.validate_range(age, self._AGE_RANGE, "age")
        if age is NA:
            return NA, NA, NA

        age_int = int(age)  # floor, consistent with rspiro
        c = self._coefficients["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]

        sspline, mspline, lspline = self._splines_at(sex, age_int, parameter)
        if pandas.isna(mspline) or pandas.isna(sspline):
            return NA, NA, NA
        return self._equation(c, age, height, sspline, mspline, lspline)

    def _sex_lms_arrays(self, sex: int, age, height, ethnicity, parameter) -> tuple:
        c = self._coefficients["%s_%ss" % (self.Parameters(parameter).name, self.Sex(sex).name.lower())]
        age, na = self._validate_range_array(age, self._AGE_RANGE, "age")
        age = numpy.where(na, self._AGE_RANGE[0], age)
        table = self._spline_table(sex, parameter)
        if table is None:
            nan = numpy.full(len(age), numpy.nan)
            return nan, nan, nan, numpy.ones(len(age), dtype=bool)
        positions = table.index.get_indexer(numpy.trunc(age))
        splines = []
        for name in ("Sspline", "Mspline", "Lspline"):
            values = table[name].to_numpy(dtype=float)[positions]
            values[positions < 0] = numpy.nan
            splines.append(values)
        sspline, mspline, lspline = splines
        na = na | numpy.isnan(mspline) | numpy.isnan(sspline)
        with numpy.errstate(all="ignore"):
            l, m, s = self._equation(c, age, height, sspline, mspline, lspline)
        return l, m, s, na


class RegressionResult:
    """
    Result of a regression equation for one row (scalars) or for the rows of
    one group (arrays): the predicted value and, where published, LLN, ULN
    and the z-score, z = (value - center) / scale, or
    (ln(value) - center) / scale if log_z. Quantities that the equation does
    not provide are None; na marks rows that are NA altogether. Subclasses
    with their own metric formulas may pass further named quantities.
    """

    FIELDS = ("pred", "lln", "uln", "center", "scale", "log_z")

    def __init__(self, pred=None, lln=None, uln=None, center=None, scale=None, log_z=False, na=False, **extra):
        self.pred, self.lln, self.uln = pred, lln, uln
        self.center, self.scale, self.log_z = center, scale, log_z
        self.na = na
        self.fields = self.FIELDS + tuple(extra)
        for name, value in extra.items():
            setattr(self, name, value)

    @classmethod
    def missing(cls):
        return cls(na=True)


class _RegressionArrays:
    """Merges the RegressionResult of row groups into whole-column arrays."""

    def __init__(self, n: int):
        self.n = n
        self.na = numpy.ones(n, dtype=bool)
        self.values = {}
        self.available = {}

    def put(self, rows, result: RegressionResult):
        self.na[rows] = result.na
        for field in result.fields:
            value = getattr(result, field)
            if value is None:
                continue
            if field not in self.values:
                dtype = numpy.asarray(value).dtype
                if dtype.kind in "iuf":
                    self.values[field] = numpy.full(self.n, numpy.nan)
                else:
                    self.values[field] = numpy.zeros(self.n, dtype=bool if dtype.kind == "b" else object)
                self.available[field] = numpy.zeros(self.n, dtype=bool)
            self.values[field][rows] = value
            self.available[field][rows] = True

    def result(self) -> RegressionResult:
        """A RegressionResult of arrays; quantities missing for some rows are NA there (see na_for())."""
        fields = dict(self.values)
        core = {f: fields.pop(f) for f in RegressionResult.FIELDS if f in fields}
        return RegressionResult(na=self.na, **core, **fields)

    def na_for(self, field: str):
        """Rows for which the quantity is NA (row NA, or not provided by the equation)."""
        if field not in self.available:
            return numpy.ones(self.n, dtype=bool)
        return self.na | ~self.available[field]


class RegressionReference(Reference):
    """
    Intermediate base for regression (non-LMS) reference equations.

    A subclass writes its equation once, in _regression(sex, age, height,
    ethnicity, weight, parameter), which returns a RegressionResult. sex,
    ethnicity and parameter are always scalars; age, height and weight are
    scalars for the scalar methods and NumPy arrays (the rows of one
    sex/ethnicity group) for the vectorised compute(). Range checks go
    through _validated(), which behaves like validate_range() for scalars.

    The scalar metrics are derived by _percent(), _zscore(), _lln() and
    _uln(); subclasses keep their public method signatures and call these.
    compute() evaluates whole columns when the class that defines
    _regression() sets _ARRAY_REGRESSION = True and the requested metric
    methods are defined in that class or above it.

    Subclasses with a coefficient table set _coeffs_csv (';'-separated, in
    pyspiro.data) and _coeffs_index; the table is loaded into
    self._coefficients and _row() returns one of its rows.
    """

    _coeffs_csv = None
    _coeffs_index = ('parameter', 'sex')

    def __init__(self):
        if self._coeffs_csv is not None:
            import importlib.resources
            with (importlib.resources.files('pyspiro.data') / self._coeffs_csv).open('rb') as f:
                self._coefficients = pandas.read_csv(f, delimiter=';').set_index(list(self._coeffs_index))

    def _row(self, key, table=None, required=False):
        """
        Row of a coefficient table (default: self._coefficients) as a dict, or
        None if the table has no such row (KeyError if required). Rows are
        cached: the tables are not changed after loading.
        """
        table = self._coefficients if table is None else table
        cache = self.__dict__.setdefault('_row_cache', {})
        cache_key = (id(table), key)
        if cache_key not in cache:
            try:
                cache[cache_key] = table.loc[key].to_dict()
            except KeyError:
                cache[cache_key] = None
        row = cache[cache_key]
        if row is None and required:
            raise KeyError(key)
        return row

    _ARRAY_REGRESSION = False
    # Type of the scalar results of _regression() (the formulas use NumPy so that they also
    # work on arrays; float keeps the Python floats, and Python's rounding, of the scalar methods)
    _SCALAR_TYPE = float

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        raise NotImplementedError

    # ── Scalar and array helpers for _regression() ─────────────────────────
    #
    # The math functions use Python's math module for the scalar methods (as these have always
    # computed) and NumPy for the arrays of compute().

    @staticmethod
    def _all_na(na) -> bool:
        return na.all() if isinstance(na, numpy.ndarray) else bool(na)

    @staticmethod
    def _exp(x):
        return numpy.exp(x) if isinstance(x, numpy.ndarray) else math.exp(x)

    @staticmethod
    def _log(x):
        return numpy.log(x) if isinstance(x, numpy.ndarray) else math.log(x)

    @staticmethod
    def _log10(x):
        return numpy.log10(x) if isinstance(x, numpy.ndarray) else math.log10(x)

    @staticmethod
    def _maximum(x, floor):
        return numpy.maximum(x, floor) if isinstance(x, numpy.ndarray) else max(x, floor)


    def _validated(self, value, value_range: tuple, value_type: str = "value", na=False) -> tuple:
        """
        validate_range() for a scalar or an array. Returns (value, na); rows
        already NA are not checked again (as the scalar code returns early).
        In arrays, NA rows get the lower limit as a placeholder.
        """
        if not isinstance(value, numpy.ndarray):
            if na:
                return value, True
            value = self.validate_range(value, value_range, value_type)
            return value, value is NA
        na = numpy.broadcast_to(na, numpy.shape(value)).copy()
        value = numpy.array(value, dtype=float)
        checked, out = self._validate_range_array(value[~na], value_range, value_type)
        value[~na] = checked
        na[~na] = out
        value[na] = value_range[0]
        return value, na

    def _per_key(self, keys, na, evaluate, *arrays) -> RegressionResult:
        """
        For coefficients that depend on the row (age group, whole-year age):
        evaluate(key, na, *arrays) for a scalar key, or once per distinct key
        on the matching non-NA rows of the arrays, merged.
        """
        if not isinstance(keys, numpy.ndarray):
            return evaluate(keys, na, *arrays)
        merged = _RegressionArrays(len(keys))
        valid = ~numpy.asarray(na)
        for key in pandas.unique(keys[valid]):
            rows = valid & (keys == key)
            merged.put(rows, evaluate(key, numpy.zeros(rows.sum(), dtype=bool), *(a[rows] for a in arrays)))
        return merged.result()

    def _notify(self, message: str, like):
        """Print message once per row, as the scalar code does per call, unless silenced."""
        if not self._silent:
            for _ in range(numpy.size(like)):
                print(message)

    # ── Scalar metrics ──────────────────────────────────────────────────────

    def _scalar_regression(self, sex, age, height, ethnicity, weight, parameter):
        """_regression() for one row with Python-typed results, or None if the row is NA."""
        r = self._regression(sex, age, height, ethnicity, weight, parameter)
        if r.na:
            return None
        for field in ("pred", "lln", "uln", "center", "scale"):
            value = getattr(r, field)
            if value is not None and value is not NA:
                setattr(r, field, self._SCALAR_TYPE(value))
        return r

    @staticmethod
    def _percent(r, value):
        return NA if r is None or r.pred is None else round(value / r.pred * 100, 2)

    @staticmethod
    def _zscore(r, value):
        if r is None or r.center is None or r.scale == 0:
            return NA
        if r.log_z:
            return (math.log(value) - r.center) / r.scale
        return (value - r.center) / r.scale

    @staticmethod
    def _lln(r):
        return NA if r is None or r.lln is None else r.lln

    @staticmethod
    def _uln(r):
        return NA if r is None or r.uln is None else r.uln

    # ── Vectorised compute() ────────────────────────────────────────────────

    def _owner(self, name):
        return next((k for k in type(self).__mro__ if name in vars(k)), None)

    def _regression_vectorised(self, metrics) -> bool:
        owner = self._owner('_regression')
        if owner is None or not vars(owner).get('_ARRAY_REGRESSION', False):
            return False
        return all(issubclass(owner, self._owner(m)) for m in metrics)

    def _regression_arrays(self, columns, parameter, ethnicity, weight) -> _RegressionArrays:
        sex = columns.sex_array
        n = len(sex)
        merged = _RegressionArrays(n)
        eth = ethnicity if ethnicity is not None else numpy.zeros(n, dtype=numpy.int64)
        groups = pandas.DataFrame({"sex": sex, "eth": eth}).groupby(["sex", "eth"], sort=True).indices
        for (sex_value, eth_value), positions in groups.items():
            rows = numpy.zeros(n, dtype=bool)
            rows[positions] = True
            with numpy.errstate(all="ignore"):
                r = self._regression(int(sex_value), columns.age_array[rows], columns.height_array[rows],
                                     int(eth_value) if ethnicity is not None else None,
                                     None if weight is None else weight[rows], parameter)
            merged.put(rows, r)
        return merged

    def _metric_from_arrays(self, metric, merged: _RegressionArrays, value, index):
        """
        The metric column from the merged results, with the expressions of
        _percent(), _zscore(), _lln() and _uln(); None hands the metric back
        to the row-wise path (inputs on which the scalar method raises).
        """
        r = merged.result()
        with numpy.errstate(all="ignore"):
            if metric == 'percent':
                na = merged.na_for('pred')
                if r.pred is None:
                    return _metric_column(numpy.full(merged.n, numpy.nan), na, index, self._SCALAR_TYPE)
                if self._SCALAR_TYPE is float:
                    if (r.pred[~na] == 0).any():
                        return None                               # ZeroDivisionError
                    # Python's round(), as on the Python floats of the scalar path
                    values = numpy.array([round(x, 2) for x in (value / r.pred * 100).tolist()], dtype=float)
                else:
                    values = numpy.round(value / r.pred * 100, 2)
            elif metric == 'zscore':
                na = merged.na_for('center') | merged.na_for('scale')
                if r.center is None:
                    return _metric_column(numpy.full(merged.n, numpy.nan), na, index, self._SCALAR_TYPE)
                na = na | (r.scale == 0)
                log_rows = ~na & r.log_z
                if (value[log_rows] <= 0).any():
                    return None                                   # math.log() raises
                x = numpy.where(log_rows, numpy.log(numpy.where(log_rows, value, 1.0)), value)
                values = (x - r.center) / r.scale
            elif metric in ('lln', 'uln'):
                na = merged.na_for(metric)
                values = getattr(r, metric)
                if values is None:
                    values = numpy.full(merged.n, numpy.nan)
            else:
                return None
        return _metric_column(values, na, index, self._SCALAR_TYPE)

    # Metrics evaluated on arrays; any other requested metric uses the row-wise path
    _VECTORISED_METRICS = ('percent', 'zscore', 'lln', 'uln')

    def compute(self, df: pandas.DataFrame, parameter: int,
                sex_col: str = 'sex', age_col: str = 'age', height_col: str = 'height',
                value_col: str = None, ethnicity_col: str = None, weight_col: str = None,
                metrics: tuple = ('percent', 'zscore', 'lln', 'uln')) -> pandas.DataFrame:
        """See Reference.compute(); whole columns are evaluated at once where possible."""
        if not self._regression_vectorised(metrics):
            return super().compute(df, parameter, sex_col, age_col, height_col, value_col,
                                   ethnicity_col, weight_col, metrics)
        params = {m: self._metric_params(m) for m in metrics}
        self._check_compute_arguments(params, value_col, weight_col)

        columns = _ComputeColumns(df, sex_col, age_col, height_col, value_col, ethnicity_col, weight_col)
        result = {}
        cache = {}
        for metric in metrics:
            column = None
            if metric in self._VECTORISED_METRICS:
                # as Reference.compute(): ethnicity 0 when the method takes it but no column is
                # given; weight and value only when the method takes them
                uses_eth = 'ethnicity' in params[metric]
                uses_weight = 'weight' in params[metric]
                key = (uses_eth, uses_weight)
                if key not in cache:
                    ethnicity = (columns.ethnicity_array() if ethnicity_col is not None
                                 else numpy.zeros(len(df), dtype=numpy.int64)) if uses_eth else None
                    weight = columns.weight_array if uses_weight else None
                    cache[key] = self._regression_arrays(columns, parameter, ethnicity, weight)
                value = columns.value_array_or(0.0) if 'value' in params[metric] else numpy.zeros(len(df))
                self._check_metric(metric, parameter, cache[key])
                column = self._metric_from_arrays(metric, cache[key], value, df.index)
            if column is None:
                column = super().compute(df, parameter, sex_col, age_col, height_col, value_col,
                                         ethnicity_col, weight_col, (metric,))[metric]
            result[metric] = column
        return pandas.DataFrame(result, index=df.index)

    def _check_metric(self, metric, parameter, merged: _RegressionArrays):
        """Hook: raise where the scalar metric method would raise for this parameter."""


class PredictedValueReference(RegressionReference):
    """
    Regression equations that publish the predicted value only: percent() is
    defined; zscore(), lln() and uln() return NA and lms() (NA, NA, NA).

    """

    def percent(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Return the measured value as % of the predicted value."""
        return self._percent(self._scalar_regression(sex, age, height, ethnicity, None, parameter), value)

    def zscore(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no residual SD was published; returns pd.NA."""
        return NA

    def lms(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not applicable — regression equation, not LMS; returns (NA, NA, NA)."""
        return NA, NA, NA

    def lln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no lower limit of normal was published; returns pd.NA."""
        return NA

    def uln(self, sex, age, height, ethnicity=None, parameter=None, value=None):
        """Not available — no upper limit of normal was published; returns pd.NA."""
        return NA


class CentileLookupReference(RegressionReference):
    """
    Equations published as look-up tables of the predicted value and the 5th
    centile on an (age, height) grid. Age and height are rounded to the grid
    (_grid()), the cell is looked up, and

        z   = (value - predicted) / ((predicted - LLN) / 1.645)   (normal approximation)
        ULN = 2 * predicted - LLN

    Subclasses set _lookup_csv (';'-separated, indexed by age and height,
    columns <parameter>_<females|males>_pv and ..._<_limit_suffix>),
    _AGE_RANGE, _HEIGHT_RANGE and _grid(); _EMPTY_CELLS_NA makes cells
    without a value NA instead of NaN.
    """

    _lookup_csv: str
    _limit_suffix: str
    _AGE_RANGE: tuple
    _HEIGHT_RANGE: tuple
    _EMPTY_CELLS_NA = False

    _ARRAY_REGRESSION = True

    def __init__(self):
        self._lookup = self._load_lookup()
        self._age_range    = self._AGE_RANGE
        self._height_range = self._HEIGHT_RANGE

    def _load_lookup(self) -> pandas.DataFrame:
        import importlib.resources
        pkg = importlib.resources.files('pyspiro.data')
        with (pkg / self._lookup_csv).open('rb') as f:
            df = pandas.read_csv(f, delimiter=';')
        df.set_index(['age', 'height'], inplace=True)
        return df

    def _grid(self, value):
        """Round a scalar or an array to the grid of the look-up table."""
        raise NotImplementedError

    def _cells(self, sex, age, height, parameter) -> tuple:
        """(predicted, limit) of the grid cells at the (already rounded) ages and heights."""
        param_name = self.Parameters(parameter).name
        sex_label  = 'females' if sex == self.Sex.FEMALE.value else 'males'
        columns = ('%s_%s_pv' % (param_name, sex_label), '%s_%s_%s' % (param_name, sex_label, self._limit_suffix))
        if not isinstance(age, numpy.ndarray):
            row = self._lookup.loc[(age, height)]
            return tuple(float(row[c]) for c in columns)
        positions = self._lookup.index.get_indexer(pandas.MultiIndex.from_arrays([age, height]))
        if (positions < 0).any():
            raise KeyError("%s: (age, height) not in the look-up table" % type(self).__name__)
        return tuple(self._lookup[c].to_numpy(dtype=float)[positions] for c in columns)

    def _regression(self, sex, age, height, ethnicity, weight, parameter) -> RegressionResult:
        age, na = self._validated(self._grid(age), self._AGE_RANGE, 'age')
        height, na = self._validated(self._grid(height), self._HEIGHT_RANGE, 'height', na)
        if self._all_na(na):
            return RegressionResult.missing()
        if isinstance(age, numpy.ndarray):
            age, height = self._grid(age), self._grid(height)     # grid type for the placeholder rows
        pv, lln = self._cells(sex, age, height, parameter)
        if self._EMPTY_CELLS_NA:
            if not isinstance(pv, numpy.ndarray):
                if math.isnan(pv) or math.isnan(lln):
                    return RegressionResult.missing()
            else:
                na = na | numpy.isnan(pv) | numpy.isnan(lln)
        return RegressionResult(pv, lln=lln, uln=2 * pv - lln, center=pv, scale=(pv - lln) / 1.645, na=na)

    def _pv_lln(self, sex, age, height, parameter) -> tuple:
        """(predicted, LLN) for one row, or (pandas.NA, pandas.NA)."""
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        return (NA, NA) if r is None else (r.pred, r.lln)

    def lms(self, sex: int, age: float, height: float, parameter: int, value: float = None) -> tuple:
        """Not applicable — direct centile look-up, not LMS; returns (NA, NA, NA)."""
        return NA, NA, NA

    def percent(self, sex: int, age: float, height: float, parameter: int, value: float) -> float:
        """Return measured value as % of the predicted median."""
        return self._percent(self._scalar_regression(sex, age, height, None, None, parameter), value)

    def zscore(self, sex: int, age: float, height: float, parameter: int, value: float) -> float:
        """Return z-score: (value - predicted) / ((predicted - LLN) / 1.645), normal approximation."""
        return self._zscore(self._scalar_regression(sex, age, height, None, None, parameter), value)

    def lln(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Return lower limit of normal (5th centile)."""
        return self._lln(self._scalar_regression(sex, age, height, None, None, parameter))

    def uln(self, sex: int, age: float, height: float, parameter: int) -> float:
        """Return upper limit of normal (95th centile), approximated as 2 x predicted - LLN."""
        return self._uln(self._scalar_regression(sex, age, height, None, None, parameter))

    def all(self, sex: int, age: float, height: float, parameter: int, value: float) -> tuple:
        """Return (percent, z-score, lln, uln) in a single call."""
        r = self._scalar_regression(sex, age, height, None, None, parameter)
        if r is None:
            return NA, NA, NA, NA
        return self._percent(r, value), self._zscore(r, value), r.lln, r.uln


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
