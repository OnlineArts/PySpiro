"""
Cross-equation comparison utilities for lung function measurements.

Provides functions to compare predicted values and z-scores across multiple
reference equations for the same patient or population.
"""

import pandas as pd
import inspect


def compare_equations(patient_record, parameter, equations=None):
    """
    Compare %predicted and z-scores across multiple equations for a single patient.

    Given a patient record with demographic and measured lung function data,
    calculate %predicted and z-score using all provided (or specified) equations.
    Useful for sensitivity analysis and understanding how equation choice affects
    clinical interpretation.

    Args:
        patient_record (dict or pd.Series): Patient data with at minimum:
            - sex (int): 0=female, 1=male
            - age (float): age in years
            - height (float): height in cm
            - <measured_value> (float): the measured lung function value
            - ethnicity (int, optional): required for ethnicity-stratified equations

        parameter (int or enum): The parameter being compared (e.g., GLI_2012.Parameters.FEV1).
                                All equations must have a parameter with the same value
                                (matching by enum value, not by name).

        equations (list, optional): List of equation instances to use (e.g., [GLI_2012(), BOWERMANN_2022()]).
                                   If None, defaults to all available equations.

    Returns:
        pd.DataFrame: Comparison table with columns:
            - equation (str): Name of the equation
            - percent_predicted (float): %predicted value or NaN if not applicable
            - zscore (float): z-score or NaN if not applicable
            - applicable (bool): True if equation supports the parameter and input is in valid range

    Raises:
        ValueError: If patient_record does not contain required fields.
        TypeError: If parameter type is incompatible.

    Example:
        >>> from pyspiro import GLI_2012, BOWERMANN_2022
        >>> import pandas as pd
        >>>
        >>> patient = pd.Series({
        ...     'sex': 1,
        ...     'age': 45,
        ...     'height': 175,
        ...     'ethnicity': 1,
        ...     'FEV1': 2.8
        ... })
        >>>
        >>> gli = GLI_2012()
        >>> bowermann = BOWERMANN_2022()
        >>> df = compare_equations(patient, gli.Parameters.FEV1, equations=[gli, bowermann])
        >>> print(df)
    """

    # Ensure patient_record is a Series for consistent access
    if isinstance(patient_record, dict):
        patient_record = pd.Series(patient_record)

    required_fields = {"sex", "age", "height"}
    if not required_fields.issubset(patient_record.index):
        missing = required_fields - set(patient_record.index)
        raise ValueError(
            f"patient_record must include {required_fields}. Missing: {missing}"
        )

    if equations is None:
        equations = _get_default_equations()

    results = []

    for eq in equations:
        eq_name = eq.__class__.__name__


        # Check if equation has the parameter
        if not _equation_has_parameter(eq, parameter):
            results.append(
                {
                    "equation": eq_name,
                    "percent_predicted": pd.NA,
                    "zscore": pd.NA,
                    "applicable": False,
                }
            )
            continue

        # Build the arguments for calling equation methods
        kwargs = _build_kwargs(
            patient_record, eq, parameter, check_ethnicity=True
        )

        if kwargs is None:
            results.append(
                {
                    "equation": eq_name,
                    "percent_predicted": pd.NA,
                    "zscore": pd.NA,
                    "applicable": False,
                }
            )
            continue

        # Get measured value (inferred from parameter name if possible)
        measured_value = _get_measured_value(patient_record, parameter, eq)

        if pd.isna(measured_value):
            results.append(
                {
                    "equation": eq_name,
                    "percent_predicted": pd.NA,
                    "zscore": pd.NA,
                    "applicable": False,
                }
            )
            continue

        # Calculate results
        pct = eq.percent(**kwargs, value=measured_value)
        z = eq.zscore(**kwargs, value=measured_value)

        results.append(
            {
                "equation": eq_name,
                "percent_predicted": pct,
                "zscore": z,
                "applicable": not pd.isna(pct),
            }
        )

    return pd.DataFrame(results)


def _equation_has_parameter(equation, parameter):
    """Check if an equation has a given parameter."""
    if hasattr(equation, "Parameters"):
        try:
            param_value = parameter.value if hasattr(parameter, 'value') else parameter
            if isinstance(param_value, int):
                enum_val = equation.Parameters(param_value)
                return True
        except (ValueError, AttributeError):
            return False
    return False


def _build_kwargs(patient_record, equation, parameter, check_ethnicity=True):
    """
    Build kwargs for calling equation methods.

    Returns a dict with: sex, age, height, ethnicity (if needed), parameter.
    Returns None if the equation cannot be applied to the patient.
    """
    # Convert parameter to its integer value to support both enum and int inputs
    param_value = parameter.value if hasattr(parameter, 'value') else parameter

    kwargs = {
        "sex": int(patient_record["sex"]),
        "age": float(patient_record["age"]),
        "height": float(patient_record["height"]),
        "parameter": param_value,
    }

    # Check the equation's lms signature to see what parameters it needs
    sig = inspect.signature(equation.lms)
    params = set(sig.parameters.keys())

    # Only add ethnicity if the equation's lms method includes it
    if "ethnicity" in params:
        if check_ethnicity and "ethnicity" not in patient_record:
            return None
        if "ethnicity" in patient_record:
            kwargs["ethnicity"] = int(patient_record["ethnicity"])

    return kwargs


def _get_measured_value(patient_record, parameter, equation):
    """
    Extract the measured value from patient_record.

    Tries to infer the column name from the parameter enum name.
    """
    if hasattr(equation, "Parameters"):
        try:
            # Convert parameter to integer value to support both enum and int inputs
            param_value = parameter.value if hasattr(parameter, 'value') else parameter
            param_name = equation.Parameters(param_value).name
            if param_name in patient_record and pd.notna(patient_record[param_name]):
                return float(patient_record[param_name])
        except (ValueError, AttributeError):
            pass

    return pd.NA


def _get_default_equations():
    """
    Return a list of all available equation instances.

    This imports all equation classes from pyspiro and instantiates them.
    """
    from .src.GLI_2012 import GLI_2012
    from .src.BOWERMANN_2022 import BOWERMANN_2022
    from .src.KUSTER_2008 import KUSTER_2008
    from .src.HANKINSON_1999 import HANKINSON_1999
    from .src.KUBOTA_2014 import KUBOTA_2014
    from .src.GLI_2017 import GLI_2017
    from .src.GLI_2021 import GLI_2021
    from .src.SCHULZ_2013 import SCHULZ_2013
    from .src.SCAPIS_2023 import SCAPIS_2023
    from .src.ATS_ERS_2022 import ATS_ERS_2022

    return [
        GLI_2012(),
        BOWERMANN_2022(),
        KUSTER_2008(),
        HANKINSON_1999(),
        KUBOTA_2014(),
        GLI_2017(),
        GLI_2021(),
        SCHULZ_2013(),
        SCAPIS_2023(),
        ATS_ERS_2022(),
    ]
