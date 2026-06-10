from abc import ABC, abstractmethod
from enum import Enum
import inspect

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
    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return the measured value as % of the predicted median."""
        pass

    @abstractmethod
    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return the z-score of the measured value relative to the reference distribution."""
        pass

    @abstractmethod
    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return the (L, M, S) triplet for the given inputs."""
        pass

    @abstractmethod
    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return the lower limit of normal (5th percentile)."""
        pass

    @abstractmethod
    def uln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        """Return the upper limit of normal (95th percentile)."""
        pass

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
                value_col: str = None, ethnicity_col: str = None,
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
        >>> bow = BOWERMANN_2022()
        >>> results = bow.compute(df, BOWERMANN_2022.Parameters.FVC, value_col='FVC')
        >>> # Custom column names — e.g. 'gender' instead of 'sex':
        >>> results = bow.compute(df, BOWERMANN_2022.Parameters.FVC,
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
    self._splines_data. The _get_splines() helper yields (Sspline, Mspline,
    Lspline) for a given sex/age/parameter combination.

    Subclasses only need to implement lms(); everything else is inherited.
    """

    _splines_csv: str
    _coeffs_csv: str

    def __init__(self):
        import importlib.resources
        lookup = pandas.read_csv(
            importlib.resources.open_binary('pyspiro.data', self._splines_csv),
            delimiter=";",
        ).set_index("age")
        splines = pandas.read_csv(
            importlib.resources.open_binary('pyspiro.data', self._coeffs_csv),
            delimiter=";",
        ).set_index("var")
        self._age_range = (min(lookup.index), max(lookup.index))
        self._lookup = lookup
        self._splines_data = splines

    def _get_splines(self, sex: int, age: float, parameter: int):
        """Yield (Sspline, Mspline, Lspline) from the age-indexed lookup table."""
        for i in ("Sspline", "Mspline", "Lspline"):
            yield self._lookup[
                "%s_%ss_%s" % (self.Parameters(parameter).name, self.Sex(sex).name.lower(), i)
            ].loc[age]


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
