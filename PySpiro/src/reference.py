from abc import ABC, abstractmethod
from enum import Enum
from pandas import NA

class Reference(ABC):

    @abstractmethod
    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float, silent: bool = True):
        pass

    @abstractmethod
    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float, silent: bool = True):
        pass

    @abstractmethod
    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float, silent: bool = True):
        pass

    @abstractmethod
    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float, silent: bool = True):
        pass

    def check_range(self, value: float, range: tuple):
        return range[0] <= value <= range[1]

    def check_tuple(self, value: float, allowed: tuple, type: "value", silent: bool = False):
        for i in allowed:
            if value == i:
                return value

        if not silent:
            print("The given %s of %.2f is not fitting to the allow values %s" % (type, value, str(allowed)))
        return NA

    def validate_range(self, value: float, range: tuple, type: str = "value", strategy: str = "ignore", silent: bool = False):
        if not self.check_range(value, range):
            if not silent:
                print("The given %s of %.2f does not fit to the defined %s range %.2f-%.2f" % (type, value, type, range[0], range[1]))

            if strategy == "closest":
                old_value = value
                if value <= range[0]:
                    value = range[0]
                else:
                    value = range[1]
                print("Set %s to %.2f from %.2f" % (type, value, old_value))
            elif "ignore":
                value = NA

        return value

    class Sex(Enum):
        FEMALE = 0
        MALE = 1