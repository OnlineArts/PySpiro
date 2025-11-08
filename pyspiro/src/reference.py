from abc import ABC, abstractmethod
from enum import Enum
from pandas import NA

class Reference(ABC):

    _strategy = "ignore"
    _silent = True

    def set_strategy(self, strategy: str):
        if strategy == "ignore" or strategy == "closest":
            self._strategy = strategy
            return True
        return False

    def set_silence(self, silent: bool):
        self._silent = silent

    def get_strategy(self):
        return self._strategy

    @abstractmethod
    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass

    @abstractmethod
    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass

    @abstractmethod
    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass

    @abstractmethod
    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
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