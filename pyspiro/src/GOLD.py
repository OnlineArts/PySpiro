import pandas as pd

from .reference import Classifier

class GOLD(Classifier):

    _order = [1, 2, 3, 4]
    _map_names = {1: "I", 2: "II", 3: "III", 4: "IV"}
    _map_meaning = {1: "mild", 2: "moderate", 3: "severe", 4: "very severe"}

    def classify(self, **kwargs):

        if len(kwargs) == 1:
            if "FEV1p" in kwargs:
                fev1 = kwargs["FEV1p"]
            else:
                print("GOLD Classifier: could not find FEV1p argument. Assuming the provided argument to be FEV1%pred)")
                fev1 = kwargs[0]
        else:
            print("GOLD Classifier: Ambiguous number of arguments, GOLD expects only FEV1%predicted as FEV1p variable")
            return pd.NA

        # Check if 80 % or 0.8 notations
        if fev1 <= 1:
            fev1 = fev1 * 100

        if fev1 >= 80:
            return 1
        elif 50 <= fev1 < 80:
            return 2
        elif 30 <= fev1 < 50:
            return 3
        elif fev1 < 30:
            return 4

        return pd.NA