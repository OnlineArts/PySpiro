import pandas
from .src.GLI_2012 import GLI_2012

class Spiro:

    def __init__(self):
        gli = GLI_2012()
        df = pandas.DataFrame(
            {"age": [2, 6, 7.15, 55, 60, 32.1], "sex": [1, 1, 1, 0, 0, 1], "height": [120, 160, 180, 130, 176, 160],
             "FEV1": [0.15, 1.241, 1.1, 0.8, 1.4, 1.2], "ethnicity": [1, 1, 1, 2, 3, 4]})
        df["GLI_2012_FEV1"] = df.apply(
            lambda x: gli.predict(x.sex, x.age, x.height, 1, gli.Parameters["FEV1"].value, x.FEV1), axis=1)

        print(df)


if __name__ == '__main__':
    Spiro()
