import pandas as pd

from .reference import Classifier

class STAR(Classifier):

    _order = [1, 2, 3, 4]
    _map_names = {1: "I", 2: "II", 3: "III", 4: "IV"}
    _map_meaning = {1: "mild", 2: "moderate", 3: "severe", 4: "very severe"}

    def classify(self, **kwargs):

        if len(kwargs) == 1:
            if "FEV1_FVC" in kwargs:
                fev1_fvc = kwargs["FEV1_FVC"]
            else:
                print("STAR Classifier: Identified only one argument, assuming FEV1/FVC")
                fev1_fvc = kwargs[0]
        elif len(kwargs) == 2:
            if "FEV1" in kwargs and "FVC" in kwargs:
                fev1_fvc = kwargs["FEV1"]/kwargs["FVC"]
            else:
                print("STAR Classifier: Identified two arguments, assuming first one is FEV1%pred and second FVC%pred")
                fev1_fvc = kwargs[0]/kwargs[1]
        else:
            print("STAR Classifier: Ambiguous number of arguments, STAR expects FEV1/FVC or both variable separately")
            return pd.NA

        # Check if 80 % or 0.8 notations
        if fev1_fvc <= 1:
            fev1_fvc = fev1_fvc * 100

        if fev1_fvc >= 70:
            print("STAR Classifier: Patient with %f FEV1/FVC ratio is not a COPD patient. NA returned" )
            return pd.NA
        elif 60 <= fev1_fvc < 70:
            return 1
        elif 50 <= fev1_fvc < 60:
            return 2
        elif 40 <= fev1_fvc < 50:
            return 3
        elif fev1_fvc < 40:
            return 4

        return pd.NA