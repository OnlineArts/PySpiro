from abc import ABC, abstractmethod
from enum import Enum

from pandas import NA

class Reference(ABC):
    """
    Abstract base class for all lung function reference equation implementations.

    Subclasses implement LMS-based (Box-Cox) or polynomial prediction equations
    for spirometry, lung volumes, diffusion capacity, or oscillometry.

    Out-of-range handling is controlled by set_strategy():
        "ignore"  (default) — returns pd.NA for out-of-range inputs.
        "closest"           — clamps to the nearest boundary value.
    """

    _strategy = "ignore"
    _silent = True

    def set_strategy(self, strategy: str):
        """Set the out-of-range handling strategy ('ignore' or 'closest')."""
        if strategy == "ignore" or strategy == "closest":
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

    def check_tuple(self, value: float, allowed: tuple, value_type: "value"):
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