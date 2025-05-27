from .src.KUSTER_2008 import KUSTER_2008
from .src.GLI_2012 import GLI_2012
from .src.GLI_2017 import GLI_2017
from .src.GLI_2021 import GLI_2021

class Spiro:

    def __init__(self):
        print("""
This is the main object of PySpiro.
Please use a specific correction function instead of the main object.
As for example for GLI_2012:

import pandas
import GLI_2012 from PySpiro

gli = GLI_2012()

df = pandas.DataFrame(
    {"age": [2, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 1, 0, 0, 1], "height": [120, 160, 180, 130, 176, 160],
     "FEV1": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2], "ethnicity": [1, 1, 1, 2, 3, 4],
     "FEF75": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2]})

df["GLI_2012_FEV1"] = df.apply(
    lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters["FEV1"].value, x.FEV1), axis=1)

df["GLI_2012_FEF75"] = df.apply(
    lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters["FEF75"].value, x.FEF75), axis=1)

print(df)
        """)
        self._kuster_2008_example()
        self._gli_2012_example()
        self._gli_2017_example()
        self._gli_2021_example()


    def _gli_2012_example(self):
        import pandas
        
        gli = GLI_2012()
        gli.set_strategy("test")

        df = pandas.DataFrame(
            {"age": [2, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 1, 0, 0, 1], "height": [120, 160, 180, 130, 176, 160],
             "FEV1": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2], "ethnicity": [1, 1, 1, 2, 3, 4],
             "FEF75": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2]})

        df["GLI_2012_FEV1"] = df.apply(
            lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters["FEV1"], x.FEV1), axis=1)

        df["GLI_2012_FEF75"] = df.apply(
            lambda x: gli.percent(x.sex, x.age, x.height, 1, gli.Parameters["FEF75"], x.FEF75), axis=1)

        print(df)

    def _kuster_2008_example(self):
        import pandas

        kuster = KUSTER_2008()
        kuster.set_silence(False)
        
        df = pandas.DataFrame(
            {"age": [47, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 2, 0, 0, 1], "height": [170, 160, 180, 130, 195, 160],
             "FEV1": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2], "ethnicity": [1, 1, 1, 2, 3, 4],
             "FEF75": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2]})

        df["KUSTER_2008_FEV1"] = df.apply(
            lambda x: kuster.percent(x.sex, x.age, x.height, 1, kuster.Parameters.FEV1, x.FEV1), axis=1)

        df["KUSTER_2008_FEV1_LLN"] = df.apply(
            lambda x: kuster.lln(x.sex, x.age, x.height, 1, kuster.Parameters.FEV1_LLN, x.FEV1), axis=1)

        print(df)

    def _gli_2017_example(self):
        import pandas
        
        gli = GLI_2017()
        gli.set_strategy("closest")

        df = pandas.DataFrame(
            {"age": [2, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 1, 0, 0, 1], "height": [120, 160, 180, 130, 176, 160],
             "KCO": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2]})

        df["GLI_2017_KCO"] = df.apply(
            lambda x: gli.percent(x.sex, x.age, x.height, gli.Parameters.KCO_SI, x.KCO), axis=1)

        print(df)

    def _gli_2021_example(self):
        import pandas
        import numpy

        gli = GLI_2021()

        numpy.random.seed(42)

        n = 10  

        df = pandas.DataFrame({
            "age": numpy.random.randint(5, 80, size=n),             
            "sex": numpy.random.choice([0, 1], size=n),             
            "height": numpy.random.normal(170, 10, size=n).round(1),
            "VC": numpy.random.normal(3.5, 0.7, size=n).round(2),   
            "RV": numpy.random.normal(1.5, 0.4, size=n).round(2),   
            "TLC": numpy.random.normal(6.0, 0.9, size=n).round(2),  
        })

        df["GLI_2021_RV_p"] = df.apply(
            lambda x: gli.percent(x.sex, x.age, x.height, gli.Parameters.RV, x.RV), axis=1)

        print(df)

if __name__ == '__main__':
    Spiro()