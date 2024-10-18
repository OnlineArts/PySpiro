from abc import ABC, abstractmethod
from enum import Enum

class Reference(ABC):

    @abstractmethod
    def predict(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
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

    def check_age_range(self, age: float):
        return self._age_range[0] <= age <= self._age_range[1]

    def validate_age(self, age: float):
        if not self.check_age_range(age):
            print("The given age of %.2f does not fit to the defined age range %.2f-%.2f" % (age, self._age_range[0], self._age_range[1]))
            if age <= self._age_range[0]:
                age = self._age_range[0]
            else:
                age = self._age_range[1]
            print("Set age to %.2f" % age)

        return age

    class Sex(Enum):
        FEMALE = 0
        MALE = 1