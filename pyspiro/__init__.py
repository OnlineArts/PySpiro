import numpy
import pandas

from .src.KUSTER_2008 import KUSTER_2008
from .src.GLI_2012 import GLI_2012
from .src.SCHULZ_2013 import SCHULZ_2013
from .src.GLI_2017 import GLI_2017
from .src.GLI_2021 import GLI_2021
from .src.BOWERMANN_2022 import BOWERMANN_2022
from .src.SCAPIS_2023 import SCAPIS_2023


class Spiro:

    def __init__(self):
        print("""
This is the main object of pyspiro.
Please use a specific correction function instead of the main object.
As for example for GLI_2012:

import pandas
import GLI_2012 from pyspiro

gli = GLI_2012()

df = pandas.DataFrame(
    {"age": [2, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 1, 0, 0, 1], "height": [120, 160, 180, 130, 176, 160],
     "FEV1": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2], "ethnicity": [1, 1, 1, 2, 3, 4],
     "FEF75": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2]})

df["GLI_2012_FEV1"] = df.apply(
    lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters["FEV1"], x.FEV1), axis=1)

df["GLI_2012_FEF75"] = df.apply(
    lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters["FEF75"], x.FEF75), axis=1)

print(df)
        """)
        numpy.random.seed(42)
        n = 10  
        self.__dataframe = pandas.DataFrame({
            "age": numpy.random.randint(5, 80, size=n),
            "sex": numpy.random.choice([0, 1], size=n),
            "height": numpy.random.normal(170, 15, size=n).round(1),
            "VC": numpy.random.normal(3.5, 0.7, size=n).round(2),
            "RV": numpy.random.normal(1.5, 0.4, size=n).round(2),
            "TLC": numpy.random.normal(6.0, 0.9, size=n).round(2),
            "FEV1": numpy.random.normal(1.5, 3.0, size=n).round(2),
            "FEF75": numpy.random.normal(1.5, 3.0, size=n).round(2),
            "KCO": numpy.random.normal(1.5, 3.0, size=n).round(2),
            "ethnicity": numpy.random.choice([1, 4], size=n),
            "X10": numpy.random.normal(3.5, 0.7, size=n).round(2),
            "weight": numpy.random.normal(75,10, size = n).round(1),
        })

        #self._kuster_2008_example()
        #self._gli_2012_example()
        #self._schulz_2013_example()
        #self._gli_2017_example()
        #self._gli_2021_example()
        #self._bowermann_2022_example()
        self._scapis_example()

        print(self.__dataframe)

    def _kuster_2008_example(self):

        kuster2008 = KUSTER_2008()
        kuster2008.set_silence(False)
        
        self.__dataframe["KUSTER_2008_FEV1"] = self.__dataframe.apply(
            lambda x: kuster2008.percent(x.sex, x.age, x.height, 1, kuster2008.Parameters.FEV1, x.FEV1), axis=1)

        self.__dataframe["KUSTER_2008_FEV1_LLN"] = self.__dataframe.apply(
            lambda x: kuster2008.lln(x.sex, x.age, x.height, 1, kuster2008.Parameters.FEV1_LLN, x.FEV1), axis=1)

    def _gli_2012_example(self):
        
        gli2012 = GLI_2012()
        gli2012.set_strategy("closest")

        self.__dataframe["GLI_2012_FEV1"] = self.__dataframe.apply(
            lambda x: gli2012.percent(x.sex, x.age, x.height, 1, gli2012.Parameters["FEV1"], x.FEV1), axis=1)

        self.__dataframe["GLI_2012_FEF75"] = self.__dataframe.apply(
            lambda x: gli2012.percent(x.sex, x.age, x.height, 1, gli2012.Parameters["FEF75"], x.FEF75), axis=1)

    def _gli_2017_example(self):
        
        gli2017 = GLI_2017()
        gli2017.set_strategy("closest")

        self.__dataframe["GLI_2017_KCO"] = self.__dataframe.apply(
            lambda x: gli2017.percent(x.sex, x.age, x.height, gli2017.Parameters.KCO_SI, x.KCO), axis=1)

    def _gli_2021_example(self):

        gli2021 = GLI_2021()

        self.__dataframe["GLI_2021_RV_p"] = self.__dataframe.apply(
            lambda x: gli2021.percent(x.sex, x.age, x.height, gli2021.Parameters.RV, x.RV), axis=1)

    def _bowermann_2022_example(self):
        
        bowermann = BOWERMANN_2022()

        self.__dataframe["BOWERMANN_FEV1_p"] = self.__dataframe.apply(
            lambda x: bowermann.percent(x.sex, x.age, x.height, bowermann.Parameters.FEV1, x.FEV1), axis=1)


    def _schulz_2013_example(self):

        schulz = SCHULZ_2013()

        self.__dataframe[["X10_05", "X10_50", "X10_95"]]  = self.__dataframe.apply(
            lambda x: pandas.Series(schulz.percentiles(x["sex"], x["age"], x["height"], x["weight"], schulz.Parameters.X10)), axis=1)

    def _scapis_example(self):

        scapis = SCAPIS_2023()
        scapis.set_strategy("closest")

        self.__dataframe["SCAPIS_FEV1_LLN"] = self.__dataframe.apply(
            lambda x: scapis.lln(x.sex, x.age, x.height, scapis.Parameters.pre_BD_FEV1, x.FEV1), axis=1)


if __name__ == '__main__':
    Spiro()