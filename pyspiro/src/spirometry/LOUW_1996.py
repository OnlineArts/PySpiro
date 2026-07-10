from ..reference import Reference
from enum import Enum
import pandas as pd


class LOUW_1996(Reference):
    """
    Louw (1996) spirometry reference equations for South African men.

    Louw, SJ, Goldin, JG, Joubert, G: Spirometry of healthy adult South African men.
    Part I. Normative values. S Afr Med J 1996; 86: 814-819.

    Linear equations using standing height in cm and age in years for South African
    adult men. This study was conducted on healthy men (black and white) free from
    noxious industrial exposure using state-of-the-art methods.

    The study provides two sets of equations based on different spirometers:
    - Autolink: Preferred equations, derived from sleeve sealed piston spirometer
    - Vitalograph: Alternative equations, derived from bellows spirometer

    Ethnicity codes:
        0 = Black
        1 = White

    Study population: 796 bank personnel in central Johannesburg (510 black men,
    286 white men; Table III). The equations were derived from the 'healthy'
    sub-group of 208 men (128 black, 80 white), aged 20-70 years.

    No LLN published; lln(), uln(), and zscore() return pd.NA.
    FEV1/FVC ratio is not directly provided; can be calculated as FEV1/FVC.

    Note: The paper incorporates sitting height in the regression analysis (Table VII),
    but the equations implemented here are the standing-height ones of Tables V and VI.

    Citation:
        Louw SJ, Goldin JG, Joubert G. Spirometry of healthy adult South African men.
        Part I. Normative values. S Afr Med J 1996;86:814-819.
    """

    class Parameters(Enum):
        FVC = 1
        FEV1 = 2

    class Spirometer(Enum):
        AUTOLINK = 1
        VITALOGRAPH = 2

    # Observed ranges of the 'healthy' group (Table III), which the equations were fitted on.
    _AGE_RANGE = (20, 70)                  # black 20-70, white 22-68
    _HEIGHT_BLACK_RANGE = (155.0, 191.0)   # cm, standing height
    _HEIGHT_WHITE_RANGE = (163.0, 206.0)   # cm, standing height

    def __init__(self, spirometer: int = Spirometer.AUTOLINK.value):
        """
        Initialize LOUW_1996 reference equations.
        
        Parameters
        ----------
        spirometer : int, optional
            Spirometer type: 1 = AUTOLINK (default, preferred), 2 = VITALOGRAPH
        """
        self._age_range = self._AGE_RANGE
        self._spirometer = self.Spirometer(spirometer)

    def _predicted_fvc_black_autolink(self, height: float, age: float) -> float:
        """FVC for black men using Autolink: 0.053 × height - 0.030 × age - 3.54"""
        return 0.053 * height - 0.030 * age - 3.54

    def _predicted_fvc_white_autolink(self, height: float, age: float) -> float:
        """FVC for white men using Autolink: 0.056 × height - 0.038 × age - 3.07"""
        return 0.056 * height - 0.038 * age - 3.07

    def _predicted_fev1_black_autolink(self, height: float, age: float) -> float:
        """FEV1 for black men using Autolink: 0.036 × height - 0.032 × age - 1.18

        The abstract prints 0.038 for the height term, Table VI prints 0.036.
        Table VI is used: evaluated at the healthy black group's mean height and age
        (169.7 cm, 41.1 y; Table III) it returns 3.61 L against the observed mean of
        3.57 L (Table IV), while 0.038 returns 3.95 L. An OLS fit with an intercept
        must reproduce the group mean, so 0.038 is a typo in the abstract.
        """
        return 0.036 * height - 0.032 * age - 1.18

    def _predicted_fev1_white_autolink(self, height: float, age: float) -> float:
        """FEV1 for white men using Autolink: 0.042 × height - 0.038 × age - 1.45"""
        return 0.042 * height - 0.038 * age - 1.45

    def _predicted_fvc_black_vitalograph(self, height: float, age: float) -> float:
        """FVC for black men using Vitalograph: 0.048 × height - 0.024 × age - 3.08"""
        return 0.048 * height - 0.024 * age - 3.08

    def _predicted_fvc_white_vitalograph(self, height: float, age: float) -> float:
        """FVC for white men using Vitalograph: 0.056 × height - 0.031 × age - 3.42"""
        return 0.056 * height - 0.031 * age - 3.42

    def _predicted_fev1_black_vitalograph(self, height: float, age: float) -> float:
        """FEV1 for black men using Vitalograph: 0.029 × height - 0.027 × age - 0.535"""
        return 0.029 * height - 0.027 * age - 0.535

    def _predicted_fev1_white_vitalograph(self, height: float, age: float) -> float:
        """FEV1 for white men using Vitalograph: 0.042 × height - 0.036 × age - 1.84"""
        return 0.042 * height - 0.036 * age - 1.84

    def _compute(self, sex: int, age: float, height: float, ethnicity: int, parameter: int) -> float:
        """Compute predicted value for given sex, age, height, ethnicity, and parameter."""
        # Validate sex - Louw 1996 is for men only
        if sex != self.Sex.MALE.value:
            if not self._silent:
                print("LOUW_1996 reference equations are only for men (sex=1).")
            return pd.NA

        # Validate ethnicity
        if ethnicity not in (0, 1):  # 0 = Black, 1 = White
            if not self._silent:
                print("LOUW_1996 ethnicity must be 0 (Black) or 1 (White).")
            return pd.NA

        # Validate age range
        age = self.validate_range(age, self._AGE_RANGE, 'age')
        if age is pd.NA:
            return pd.NA

        # Validate height range
        h_range = self._HEIGHT_BLACK_RANGE if ethnicity == 0 else self._HEIGHT_WHITE_RANGE
        height = self.validate_range(height, h_range, 'height')
        if height is pd.NA:
            return pd.NA

        param = self.Parameters(parameter)
        
        if self._spirometer == self.Spirometer.AUTOLINK:
            if param == self.Parameters.FVC:
                if ethnicity == 0:  # Black
                    return self._predicted_fvc_black_autolink(height, age)
                else:  # White
                    return self._predicted_fvc_white_autolink(height, age)
            elif param == self.Parameters.FEV1:
                if ethnicity == 0:  # Black
                    return self._predicted_fev1_black_autolink(height, age)
                else:  # White
                    return self._predicted_fev1_white_autolink(height, age)
        
        elif self._spirometer == self.Spirometer.VITALOGRAPH:
            if param == self.Parameters.FVC:
                if ethnicity == 0:  # Black
                    return self._predicted_fvc_black_vitalograph(height, age)
                else:  # White
                    return self._predicted_fvc_white_vitalograph(height, age)
            elif param == self.Parameters.FEV1:
                if ethnicity == 0:  # Black
                    return self._predicted_fev1_black_vitalograph(height, age)
                else:  # White
                    return self._predicted_fev1_white_vitalograph(height, age)
        
        return pd.NA

    def percent(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the measured value as % of the predicted median."""
        if ethnicity is None:
            if not self._silent:
                print("LOUW_1996 requires ethnicity parameter (0=Black, 1=White).")
            return pd.NA
        if parameter is None:
            if not self._silent:
                print("LOUW_1996 requires parameter (FVC=1, FEV1=2).")
            return pd.NA
        if value is None:
            if not self._silent:
                print("LOUW_1996 percent() requires a measured value.")
            return pd.NA
            
        pred = self._compute(sex, age, height, ethnicity, parameter)
        if pred is pd.NA or value is None:
            return pd.NA
        return round((value / pred) * 100, 2)

    def zscore(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the z-score. Not available for LOUW_1996; returns pd.NA."""
        return pd.NA

    def lms(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the (L, M, S) triplet. Not available for LOUW_1996; returns pd.NA."""
        return pd.NA, pd.NA, pd.NA

    def lln(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the lower limit of normal. Not available for LOUW_1996; returns pd.NA."""
        return pd.NA

    def uln(self, sex: int, age: float, height: float, ethnicity: int = None, parameter: int = None, value: float = None):
        """Return the upper limit of normal. Not available for LOUW_1996; returns pd.NA."""
        return pd.NA