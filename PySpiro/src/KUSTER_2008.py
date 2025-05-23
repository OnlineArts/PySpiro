from .reference import Reference
from enum import Enum
import numpy as np
import pandas as pd


class KUSTER_2008(Reference):
    """
    A 2008 ERJ publication establishing reference values for lung function screening in ~8500 patients from the swiss LuftiBus trial.

    The ranges of application for these reference equations are ages 18-80 yrs and heights of 140-200 and 130-190 cm in males and 
    females, respectively.

    Kuster SP, Kuster D, Schindler C, Rochat MK, Braun J, Held L, Brändli O. Reference equations for lung 
    function screening of healthy never-smoking adults aged 18-80 years. Eur Respir J. 2008 Apr;31(4):860-8. 
    doi: 10.1183/09031936.00091407. Epub 2007 Dec 5. PMID: 18057057.
    """

    class Parameters(Enum):
        FVC = 1
        FVC_LLN = 2
        FEV1 = 3
        FEV1_LLN = 4
        MEF75 = 5
        MEF75_LLN = 6
        MEF50 = 7
        MEF50_LLN = 8
        MEF25 = 9
        MEF25_LLN = 10
        FEV1_FVC_P = 11
        FEV1_FVC_LLN = 12
        PEF = 13
        PEF_LLN = 14

    def __init__(self):
        self._age_range = (18, 80)
        self._height_female_range = (130, 190)
        self._height_male_range = (140, 200)

    def lms(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float) -> tuple:
        pass

    def zscore(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float):
        pass

    def _check_conditions(self, sex: int, age: float, height: float, silent: bool = True):
        age = self.validate_range(round(age * 4) / 4, self._age_range, "age", "ignore", silent)
        height_range = self._height_female_range if sex == self.Sex["FEMALE"].value else self._height_male_range
        height = self.validate_range(height, height_range, "height", "ignore", silent)
        sex = self.check_tuple(sex, (0,1), "sex", False)
        return age, height, sex

    def percent(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float, silent: bool = True):
        """
        In this case, only calculate the m (predicted value).
        """
        age, height, sex = self._check_conditions(sex, age, height, silent)
        if age is pd.NA or height is pd.NA or sex is pd.NA:
            return pd.NA

        if sex == self.Sex["FEMALE"].value:

            match parameter:
                case self.Parameters.FVC:
                    # FVC L = exp(-9.069+2.013 ln(H)+0.00847 A-0.000155A2)
                    m = np.exp( -9.069 + 2.013 * np.log(height) + 0.00847 * (age) - 0.000155 * (age ** 2) )
                case self.Parameters.FEV1:
                    # FEV1 L = exp(-8.397+1.865 ln(H)+0.00570 A-0.000150A2)
                    m = np.exp( -8.397 + 1.865 * np.log(height) + 0.00570 * (age) - 0.000150 * (age ** 2) )
                case self.Parameters.MEF75:
                    # MEF75 L·s−1 = exp(-2.716+0.867 ln(H)+0.00963 A-0.000140A2)
                    m = np.exp( -2.716 + 0.867 * np.log(height) + 0.00963 * (age) - 0.000140 * (age ** 2) )
                case self.Parameters.MEF50:
                    # MEF50 L·s−1 = exp(-2.131+0.674 ln(H)+0.00895 A-0.000180A2)
                    m = np.exp( -2.131 + 0.674 * np.log(height) + 0.00895 * (age) - 0.000180 * (age ** 2) )
                case self.Parameters.MEF25:
                    # MEF25 L·s−1 = exp(-4.861+1.145 ln(H)-0.01120 A-0.000096A2)
                    m = np.exp( -4.861 + 1.145 * np.log(height) - 0.01120 * (age) - 0.000096 * (age ** 2) )
                case self.Parameters.FEV1_FVC_P:
                    # FEV1/FVC % =  exp(+5.637-0.219 ln(H)-0.00249 A+0.000004A2)
                    m = np.exp( 5.637 - 0.219 * np.log(height) - 0.00249 * (age) + 0.000004 * (age ** 2) )
                case self.Parameters.PEF:
                    # PEF L·s−1 = exp(-4.794+1.316 ln(H)+0.00926 A-0.000143A2)
                    m = np.exp( -4.794 + 1.316 * np.log(height) + 0.00926 * (age) - 0.000143 * (age ** 2) )
            return round(( value / m ) * 100, 2)

        elif sex == self.Sex["MALE"].value:

            match parameter:
                case self.Parameters.FVC:
                    # FVC L = exp(-10.258+2.280 ln(H)+0.00676A-0.000124A2)
                    m = np.exp( -10.258 + 2.280 * np.log(height) + 0.00676 * (age) - 0.000124 * (age ** 2) )
                case self.Parameters.FEV1:
                    # FEV1 L = exp(-8.957+2.014 ln(H)+0.00281A-0.000105A2)
                    m = np.exp( -8.957 + 2.014 * np.log(height) + 0.00281 * (age) - 0.000105 * (age ** 2) )
                case self.Parameters.MEF75:
                    # MEF75 L·s−1 = exp(-2.227+0.812 ln(H)+0.00977A-0.000132A2)
                    m = np.exp( -2.227 + 0.812 * np.log(height) + 0.00977 * (age) - 0.000132 * (age ** 2) )
                case self.Parameters.MEF50:
                    # MEF50 L·s−1 = exp(-3.055+0.911 ln(H)+0.00249A-0.000109A2)
                    m = np.exp( -3.055 + 0.911 * np.log(height) - 0.00249 * (age) - 0.000109 * (age ** 2) )
                case self.Parameters.MEF25:
                    # MEF25 L·s−1 = exp(-3.970+1.009 ln(H)-0.01645A-0.000020A2)
                    m = np.exp( -3.970 + 1.009 * np.log(height) - 0.01645 * (age) -0.000020 * (age ** 2) )
                case self.Parameters.FEV1_FVC_P:
                    # FEV1/FVC % = exp(+6.291-0.341 ln(H)-0.00441A+0.000026A2)
                    m = np.exp( 6.291 - 0.341 * np.log(height) - 0.00441 * (age) + 0.000026 * (age ** 2) ) 
                case self.Parameters.PEF:
                    # PEF L·s−1 = exp(-3.760+1.170 ln(H)+0.00706A-0.000110A2)
                    m = np.exp( -3.760 + 1.170 * np.log(height) + 0.00706 * (age) - 0.000110 * (age ** 2) )
            return round(( value / m ) * 100, 2)


    def lln(self, sex: int, age: float, height: float, ethnicity: int, parameter: int, value: float, silent = True):
        age, height, sex = self._check_conditions(sex, age, height, silent)
        if age is pd.NA or height is pd.NA or sex is pd.NA:
            return pd.NA

        if sex == self.Sex["FEMALE"].value:

            match parameter:
                case self.Parameters.FVC_LLN:
                    # FVC L = exp(-9.213 + 2.013 ln(H) + 0.00616A - 0.000155A^2)
                    lln = np.exp( -9.213 + 2.013 * np.log(height) + 0.00616 * (age) - 0.000155 * (age ** 2) )
                case self.Parameters.FEV1_LLN:
                    # FEV1 L = exp(-8.521 + 1.865 ln(H) + 0.00357A - 0.000150A^2)
                    lln = np.exp( -8.521 + 1.865 * np.log(height) + 0.00357 * (age) - 0.000150 * (age ** 2) )
                case self.Parameters.MEF75_LLN:
                    # MEF75 L·s−1 = exp(-2.977 + 0.867 ln(H) + 0.00698A - 0.000140A^2)
                    lln = np.exp( -2.977 + 0.867 * np.log(height) + 0.00698 * (age) - 0.000140 * (age ** 2) )
                case self.Parameters.MEF50_LLN:
                    # MEF50 L·s−1 = exp(-2.374 + 0.674 ln(H) + 0.00330A - 0.000180A^2)
                    lln = np.exp( -2.374 + 0.674 * np.log(height) + 0.00330 * (age) - 0.000180 * (age ** 2) )
                case self.Parameters.MEF25_LLN:
                    # MEF25 L·s−1 = exp(-5.140 + 1.145 ln(H) - 0.02002A - 0.000096A^2)
                    lln = np.exp( -5.140 + 1.145 * np.log(height) - 0.02002 * (age) - 0.000096 * (age ** 2) )
                case self.Parameters.FEV1_FVC_LLN:
                    # FEV1/FVC % =	exp(+5.524-0.219 ln(H)-0.00313A+0.000004A2)
                    lln = np.exp( 5.524 - 0.219 * np.log(height) - 0.00313 * (age) + 0.000004 * (age ** 2) )
                case self.Parameters.PEF_LLN:
                    # PEF L·s−1 = exp(-5.032+1.316 ln(H)+0.00767A-0.000143A2)
                    lln = np.exp( -5.032 + 1.316 * np.log(height) + 0.00767 * (age) - 0.000143 * (age ** 2) )
            return lln

        elif sex == self.Sex["MALE"].value:

            match parameter:
                case self.Parameters.FVC_LLN:
                    # FVC L = exp(-10.437 + 2.280 ln(H) + 0.00532A - 0.000124A^2)
                    lln = np.exp( -10.437 + 2.280 * np.log(height) + 0.00532 * (age) - 0.000124 * (age ** 2) )
                case self.Parameters.FEV1_LLN:
                    # FEV1 L = exp(-9.111 + 2.014 ln(H) + 0.00102A - 0.000105A^2)
                    lln = np.exp(-9.111 + 2.014 * np.log(height) + 0.00102 * (age) - 0.000105 * (age ** 2) )
                case self.Parameters.MEF75_LLN:
                    # MEF75 L·s−1 = exp(-2.524 + 0.812 ln(H) + 0.00661A - 0.000132A^2)
                    lln = np.exp(- 2.524 + 0.812 * np.log(height) + 0.00661 * (age) - 0.000132 * (age ** 2) )
                case self.Parameters.MEF50_LLN:
                    # MEF50 L·s−1 = exp(-3.338 + 0.911 ln(H) - 0.00289A - 0.000109A^2)
                    lln = np.exp( -3.338 + 0.911 * np.log(height) - 0.00289 * (age) - 0.000109 * (age ** 2) )
                case self.Parameters.MEF25_LLN:
                    # MEF25 L·s−1 = exp(-4.262 + 1.009 ln(H) - 0.02485A - 0.000020A^2)
                    lln = np.exp( -4.262 + 1.009 * np.log(height) - 0.02485 * (age) -0.000020 * (age ** 2) )
                case self.Parameters.FEV1_FVC_LLN:
                    # FEV1/FVC % = exp(+6.180 - 0.341 ln(H) - 0.00529A + 0.000026A^
                    lln = np.exp( 6.180 - 0.341 * np.log(height) - 0.00529 * (age) + 0.000026 * (age ** 2) ) 
                case self.Parameters.PEF_LLN:
                    # PEF L·s−1 = exp(-3.992+1.170 ln(H)+0.00493A-0.000110A2)
                    lln = np.exp( -3.992 + 1.170 * np.log(height) + 0.00493 * (age) - 0.000110 * (age ** 2) )
            return lln