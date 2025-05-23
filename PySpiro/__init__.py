from .src.GLI_2012 import GLI_2012
from .src.KUSTER_2008 import KUSTER_2008

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
        self._gli_2012_example()
        self._kuster_2008_example()


    def _gli_2012_example(self):
        import pandas
        
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

    def _kuster_2008_example(self):
        import pandas

        kuster = KUSTER_2008()
        df = pandas.DataFrame(
            {"age": [47, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 2, 0, 0, 1], "height": [170, 160, 180, 130, 195, 160],
             "FEV1": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2], "ethnicity": [1, 1, 1, 2, 3, 4],
             "FEF75": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2]})

        df["KUSTER_2008_FEV1"] = df.apply(
            lambda x: kuster.percent(x.sex, x.age, x.height, 1, kuster.Parameters.FEV1, x.FEV1, silent=False), axis=1)

        df["KUSTER_2008_FEV1_LLN"] = df.apply(
            lambda x: kuster.lln(x.sex, x.age, x.height, 1, kuster.Parameters.FEV1_LLN, x.FEV1), axis=1)

        print(df)

if __name__ == '__main__':
    Spiro()