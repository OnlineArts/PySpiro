from enum import Enum
import pandas as pd


class KOEGELENBERG_2013:
    """
    South African Thoracic Society (SATS) correction factors for European-based spirometry
    predictions.

    Koegelenberg, CFN, Swart, F, Irusen, EM: Prediction equations for spirometry in South
    Africa. S Afr Med J 2013; 103(9): 597. DOI: 10.7196/SAMJ.7298

    Quanjer et al. (GLI 2012) confirmed that, relative to Europeans, the FEV1/FVC ratio is
    similar in people of black and Asian descent, but that both FEV1 and FVC are around 90%
    of the European predicted value. To avoid over-diagnosing restrictive impairment, SATS
    proposes multiplying European-based predicted values (e.g. ECSC / Quanjer 1993) by:

        0.90  for black and Asian individuals
        0.95  for individuals of mixed ethnicity

    Ethnicity codes:
        0 = Black or Asian
        1 = Mixed ethnicity

    This is not a reference equation. It carries no prediction equation of its own and is
    deliberately not a Reference subclass: there is nothing to take a percent, z-score or
    limit of normal from. Apply the factor to another module's predicted value, e.g.

        corrected = KOEGELENBERG_2013().correct(ecsc_predicted, ethnicity=0)

    Validation: van Rooyen et al. (Heart Lung Circ 2015; 24: 573-582) applied the 0.9 factor
    to Quanjer 1993 predictions in 2010 black South Africans from the PURE study; their
    Table 1 'correction factor' rows reproduce exactly to 0.9 x predicted. Prefer a South
    African equation (MOKOETLE_1994, LOUW_1996) over a corrected European one where the
    subject falls inside its range.

    Citation:
        Koegelenberg CFN, Swart F, Irusen EM. Prediction equations for spirometry in
        South Africa. S Afr Med J 2013;103(9):597.
        DOI: 10.7196/SAMJ.7298
    """

    BLACK_OR_ASIAN = 0.9
    MIXED_ETHNICITY = 0.95

    _silent = True

    class Ethnicity(Enum):
        BLACK_OR_ASIAN = 0
        MIXED = 1

    _FACTORS = {
        Ethnicity.BLACK_OR_ASIAN.value: BLACK_OR_ASIAN,
        Ethnicity.MIXED.value: MIXED_ETHNICITY,
    }

    def set_silence(self, silent: bool):
        self._silent = silent

    def get_correction_factor(self, ethnicity: int) -> float:
        """
        Return the SATS correction factor for a European-based prediction.

        Parameters
        ----------
        ethnicity : int
            0 = Black or Asian, 1 = Mixed ethnicity

        Returns
        -------
        float
            0.9 or 0.95; pd.NA if the ethnicity code is unknown.
        """
        if ethnicity in self._FACTORS:
            return self._FACTORS[ethnicity]
        if not self._silent:
            print("KOEGELENBERG_2013: ethnicity must be 0 (Black or Asian) or 1 (Mixed).")
        return pd.NA

    def correct(self, predicted: float, ethnicity: int) -> float:
        """
        Scale a European-based predicted value by the SATS correction factor.

        A 45-year-old Asian male with an ECSC-predicted FEV1 of 3.0 L is corrected to
        2.7 L (3.0 x 0.9).

        Parameters
        ----------
        predicted : float
            Predicted value from a European-based equation (e.g. ECSC_1993).
        ethnicity : int
            0 = Black or Asian, 1 = Mixed ethnicity

        Returns
        -------
        float
            The corrected predicted value; pd.NA if either argument is missing or unknown.
        """
        factor = self.get_correction_factor(ethnicity)
        if pd.isna(factor) or predicted is None or pd.isna(predicted):
            return pd.NA
        return predicted * factor
