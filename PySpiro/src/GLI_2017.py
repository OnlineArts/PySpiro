from PySpiro.src.reference import Reference
from enum import Enum


class GLI_2017(Reference):

    class Parameters(Enum):
        TLCO = 1
        KCO = 2
        VA = 3

    def __init__(self):
        self.__lookup = self.__load_lookup_table()

    def __load_lookup_table(self) -> tuple:
        pass
        #self._age_range: tuple = (min(lookup.index), max(lookup.index))
        #return lookup, splines


    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        pass

    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass

    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass

    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass