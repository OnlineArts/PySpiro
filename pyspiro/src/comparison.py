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
                                Matching across equations is done by parameter *name*
                                (e.g. "FEV1"), since the integer enum values are not
                                harmonised across equation classes. Passing an enum member
                                is therefore recommended; a bare integer is resolved against
                                each equation's own enum by value (single-equation use only).

        equations (list, optional): List of equation instances to use (e.g., [GLI_2012(), BOWERMAN_2022()]).
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
        >>> from pyspiro import GLI_2012, BOWERMAN_2022
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
        >>> bowerman = BOWERMAN_2022()
        >>> df = compare_equations(patient, gli.Parameters.FEV1, equations=[gli, bowerman])
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

    # Match across equations by parameter *name* (e.g. "FEV1"). Integer enum
    # values are NOT harmonised across equation classes — e.g. value 1 is FEV1
    # in GLI_2012 but FVC in HANKINSON_1999 — so matching by value silently
    # compares the wrong physiological parameter.
    param_name = getattr(parameter, "name", None)

    results = []

    def _not_applicable(name):
        return {
            "equation": name,
            "percent_predicted": pd.NA,
            "zscore": pd.NA,
            "applicable": False,
        }

    for eq in equations:
        eq_name = eq.__class__.__name__

        # Resolve this equation's own parameter member matching the request.
        eq_param = _resolve_equation_parameter(eq, parameter, param_name)
        if eq_param is None:
            results.append(_not_applicable(eq_name))
            continue

        # Build the arguments for calling equation methods
        kwargs = _build_kwargs(patient_record, eq, eq_param)
        if kwargs is None:
            results.append(_not_applicable(eq_name))
            continue

        # Get measured value (looked up by the canonical parameter name)
        measured_value = _get_measured_value(patient_record, eq_param, param_name)
        if pd.isna(measured_value):
            results.append(_not_applicable(eq_name))
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


def _resolve_equation_parameter(equation, parameter, param_name):
    """
    Return the equation's own ``Parameters`` member for the requested parameter.

    Matching is by name (preferred, so the same physiological parameter is
    compared across equations despite differing enum integer values). For a bare
    integer parameter the value is resolved within this equation only. Returns
    ``None`` if the equation has no ``Parameters`` enum or lacks the parameter.
    """
    if not hasattr(equation, "Parameters"):
        return None

    if param_name is not None:
        return equation.Parameters.__members__.get(param_name)

    # Fallback: bare integer parameter — resolve within this equation by value.
    try:
        return equation.Parameters(int(parameter))
    except (ValueError, TypeError):
        return None


def _build_kwargs(patient_record, equation, eq_param):
    """
    Build kwargs for calling equation methods.

    Returns a dict with: sex, age, height, ethnicity (if needed), parameter.
    Returns None if the equation cannot be applied to the patient.
    """
    kwargs = {
        "sex": int(patient_record["sex"]),
        "age": float(patient_record["age"]),
        "height": float(patient_record["height"]),
        "parameter": eq_param,
    }

    # Only add ethnicity if the equation's lms method includes it
    if "ethnicity" in inspect.signature(equation.lms).parameters:
        if "ethnicity" not in patient_record:
            return None
        kwargs["ethnicity"] = int(patient_record["ethnicity"])

    return kwargs


def _get_measured_value(patient_record, eq_param, param_name):
    """
    Extract the measured value from patient_record, looked up by the canonical
    parameter name (so every equation reads the same patient column).
    """
    name = param_name if param_name is not None else eq_param.name
    if name in patient_record and pd.notna(patient_record[name]):
        return float(patient_record[name])
    return pd.NA


def _get_default_equations():
    """
    Return a list of all available equation instances.

    This imports all equation classes from pyspiro and instantiates them.
    """
    from .spirometry.GLI_2012 import GLI_2012
    from .spirometry.BOWERMAN_2022 import BOWERMAN_2022
    from .spirometry.KUSTER_2008 import KUSTER_2008
    from .spirometry.HANKINSON_1999 import HANKINSON_1999
    from .spirometry.KUBOTA_2014 import KUBOTA_2014
    from .diffusion.GLI_2017 import GLI_2017
    from .volumes.GLI_2021 import GLI_2021
    from .oscillometry.SCHULZ_2013 import SCHULZ_2013
    from .diffusion.SCAPIS_2023 import SCAPIS_2023
    from .classifiers.ATS_ERS_2022 import ATS_ERS_2022

    return [
        GLI_2012(),
        BOWERMAN_2022(),
        KUSTER_2008(),
        HANKINSON_1999(),
        KUBOTA_2014(),
        GLI_2017(),
        GLI_2021(),
        SCHULZ_2013(),
        SCAPIS_2023(),
        ATS_ERS_2022(),
    ]
