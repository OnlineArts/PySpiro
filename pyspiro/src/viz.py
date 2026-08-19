"""
Visualization utilities for lung function reference equations.

Provides functions for generating centile (percentile) curves that illustrate
reference populations across age ranges.
"""

import numpy as np
import pandas as pd


def _lms_at(equation, sex, age, height, parameter, ethnicity):
    """Call equation.lms() with or without ethnicity, whichever it accepts."""
    try:
        if ethnicity is not None:
            return equation.lms(sex, age, height, ethnicity, parameter, 0)
        return equation.lms(sex, age, height, parameter, 0)
    except TypeError:
        return equation.lms(sex, age, height, parameter, 0)


def _centile_curve(equation, sex, height, parameter, ethnicity, ages, z):
    """
    Return the centile at z-score ``z`` for each age, as a numpy array.

    Ages the equation cannot score come back as np.nan so the curve breaks
    rather than being drawn through a gap.
    """
    values = []
    for age in ages:
        l, m, s = _lms_at(equation, sex, age, height, parameter, ethnicity)
        if pd.isna(l) or pd.isna(m) or pd.isna(s):
            values.append(np.nan)
        elif l != 0:
            values.append(m * ((1 + z * l * s) ** (1 / l)))
        else:
            values.append(m * np.exp(z * s))
    return np.asarray(values, dtype=float)


def plot_centile_curves(
    equation,
    sex,
    height,
    parameter,
    ethnicity=None,
    age_range=None,
    percentiles=None,
    title=None,
    figsize=(12, 7),
    ax=None,
):
    """
    Plot predicted percentile curves for a lung function parameter.

    Generates a matplotlib figure showing the 5th, 25th, 50th, 75th, and 95th
    percentile curves across the age range supported by the equation. Useful for
    visualizing reference populations in clinical papers and presentations.

    Args:
        equation: A pyspiro equation instance (e.g., GLI_2012(), BOWERMAN_2022()).
        sex (int): Sex of reference individual (0=female, 1=male).
        height (float): Height in cm.
        parameter: Parameter enum or int (e.g., GLI_2012.Parameters.FEV1).
        ethnicity (int, optional): Ethnicity code (required for multi-ethnic equations).
                                   Not needed for race-neutral equations.
        age_range (tuple, optional): (min_age, max_age) to plot. Defaults to equation's range.
        percentiles (list, optional): Percentiles to plot. Default: [5, 25, 50, 75, 95].
        title (str, optional): Chart title. Auto-generated if None.
        figsize (tuple, optional): Figure size (width, height). Default: (12, 7).
        ax (matplotlib.axes.Axes, optional): Existing axes to plot on. If None, creates new figure.

    Returns:
        matplotlib.figure.Figure: The figure object. Use plt.show() or fig.savefig() to display/save.

    Raises:
        ImportError: If matplotlib is not installed.
        ValueError: If parameter is not supported by the equation.
        TypeError: If ethnicity is required but not provided.

    Example:
        >>> from pyspiro import GLI_2012
        >>> import matplotlib.pyplot as plt
        >>> gli = GLI_2012()
        >>> fig = plot_centile_curves(
        ...     gli,
        ...     sex=1,  # male
        ...     height=175,
        ...     ethnicity=1,  # Caucasian
        ...     parameter=gli.Parameters.FEV1,
        ...     title="FEV1 Percentiles (Male, 175 cm, Caucasian)"
        ... )
        >>> plt.show()
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. Install with: pip install matplotlib"
        )

    if percentiles is None:
        percentiles = [5, 25, 50, 75, 95]

    if age_range is None:
        age_range = equation._age_range

    ages = np.linspace(age_range[0], age_range[1], 100)

    # Convert percentiles to z-scores using inverse normal CDF
    from scipy import stats

    z_scores = {}
    for p in percentiles:
        z_scores[p] = stats.norm.ppf(p / 100.0)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Define colors and linestyles for standard percentiles, with fallbacks for custom ones
    standard_colors = {5: "#d62728", 25: "#ff7f0e", 50: "#2ca02c", 75: "#1f77b4", 95: "#9467bd"}
    standard_linestyles = {5: "--", 25: "--", 50: "-", 75: "--", 95: "--"}

    # Generate colors for all percentiles
    try:
        import matplotlib
        cmap = matplotlib.colormaps['viridis']   # matplotlib >= 3.6
    except (AttributeError, KeyError):
        import matplotlib.cm as cm               # older matplotlib
        cmap = cm.get_cmap('viridis')
    colors = {}
    for p in percentiles:
        if p in standard_colors:
            colors[p] = standard_colors[p]
        else:
            # Map to [0, 1] range
            colors[p] = cmap((p - min(percentiles)) / (max(percentiles) - min(percentiles)))

    # Generate linestyles for all percentiles
    linestyles = {}
    for p in percentiles:
        if p in standard_linestyles:
            linestyles[p] = standard_linestyles[p]
        else:
            # Use solid line for non-standard percentiles
            linestyles[p] = "-"

    for percentile in percentiles:
        values = _centile_curve(equation, sex, height, parameter, ethnicity,
                                ages, z_scores[percentile])

        label = f"{percentile}th percentile"
        ax.plot(
            ages,
            values,
            label=label,
            linewidth=2,
            linestyle=linestyles[percentile],
            color=colors[percentile],
        )

    ax.set_xlabel("Age (years)", fontsize=12)
    ax.set_ylabel("FEV1 (L)", fontsize=12)
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)

    if title is None:
        sex_label = "Male" if sex == 1 else "Female"
        equation_name = equation.__class__.__name__
        title = f"{equation_name} Percentiles ({sex_label}, {height} cm)"

    ax.set_title(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    return fig


def plot_quotient_centiles(
    equation,
    quotient,
    sex,
    height,
    parameter,
    quotient_parameter=None,
    ethnicity=None,
    age_range=None,
    percentiles=None,
    bands=None,
    title=None,
    figsize=(12, 7),
    ax=None,
):
    """
    Plot a reference equation's centile curves on a physiological quotient axis.

    The centiles come from the equation; the quotient supplies only the constant
    denominator and the horizontal band grid. Reading the two together answers a
    question neither answers alone: what a given quotient is worth at each age.

    A quotient has no distribution of its own -- it is a measured value divided
    by a fixed 1st percentile -- so this is deliberately *not* a centile chart of
    the quotient. Rescaling the y-axis alone would be a relabelling of
    ``plot_centile_curves()`` and would show nothing new; the band grid is the
    point of the chart. Expect the curves to fall across age even though the
    denominator does not: an FEV1Q of 4 sits far below the lower limit of normal
    for a young adult and above it for an elderly one.

    Args:
        equation: A pyspiro equation instance supplying the centiles
                  (e.g. BOWERMAN_2022(), GLI_2017(), GLI_2021()).
        quotient: A quotient instance supplying the denominator
                  (e.g. KNOX_BROWN_2026()).
        sex (int): 0 = female, 1 = male.
        height (float): Height in cm.
        parameter: The equation's Parameters member (e.g. BOWERMAN_2022.Parameters.FEV1).
        quotient_parameter (optional): The quotient's Parameters member. If None,
                  it is resolved from ``parameter`` by name. Pass it explicitly
                  where the names differ -- GLI_2017 calls the SI transfer factor
                  TLCO, the quotient calls it DLCO_SI.
        ethnicity (int, optional): Ethnicity code, for equations that take one.
        age_range (tuple, optional): (min_age, max_age). Defaults to the
                  equation's own range.
        percentiles (list, optional): Centiles to draw. Default: [5, 25, 50, 75, 95].
        bands (iterable, optional): Quotient values to draw as horizontal
                  reference lines. Default: 1 to the quotient's MAX_BAND.
                  Pass an empty sequence to omit the grid.
        title (str, optional): Chart title. Auto-generated if None.
        figsize (tuple, optional): Figure size. Default: (12, 7).
        ax (matplotlib.axes.Axes, optional): Existing axes to plot on.

    Returns:
        matplotlib.figure.Figure: The figure object.

    Raises:
        ImportError: If matplotlib is not installed.
        ValueError: If the quotient parameter cannot be resolved, or the
                    quotient's denominator is undefined for the given sex.

    Example:
        >>> from pyspiro import BOWERMAN_2022, KNOX_BROWN_2026
        >>> import matplotlib.pyplot as plt
        >>> fig = plot_quotient_centiles(
        ...     BOWERMAN_2022(),
        ...     KNOX_BROWN_2026(),
        ...     sex=1,
        ...     height=175,
        ...     parameter=BOWERMAN_2022.Parameters.FEV1,
        ... )
        >>> plt.show()
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. Install with: pip install matplotlib"
        )

    from scipy import stats

    # Resolve the quotient's own parameter member, by name unless given.
    if quotient_parameter is None:
        param_name = getattr(parameter, "name", None)
        quotient_parameter = quotient.Parameters.__members__.get(param_name)
        if quotient_parameter is None:
            raise ValueError(
                f"cannot resolve a {type(quotient).__name__} parameter matching "
                f"{param_name!r}; pass quotient_parameter= explicitly."
            )

    denominator = quotient.percentile1(quotient_parameter, sex)
    if pd.isna(denominator):
        raise ValueError(
            f"{type(quotient).__name__} has no 1st percentile for "
            f"{getattr(quotient_parameter, 'name', quotient_parameter)} at sex={sex!r}."
        )

    if percentiles is None:
        percentiles = [5, 25, 50, 75, 95]
    if age_range is None:
        age_range = equation._age_range
    if bands is None:
        bands = range(1, getattr(quotient, "MAX_BAND", 6) + 1)

    ages = np.linspace(age_range[0], age_range[1], 100)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    standard_colors = {5: "#d62728", 25: "#ff7f0e", 50: "#2ca02c", 75: "#1f77b4", 95: "#9467bd"}
    standard_linestyles = {5: "--", 25: "--", 50: "-", 75: "--", 95: "--"}

    try:
        import matplotlib
        cmap = matplotlib.colormaps['viridis']   # matplotlib >= 3.6
    except (AttributeError, KeyError):
        import matplotlib.cm as cm               # older matplotlib
        cmap = cm.get_cmap('viridis')

    colors, linestyles = {}, {}
    for p in percentiles:
        if p in standard_colors:
            colors[p] = standard_colors[p]
        else:
            spread = max(percentiles) - min(percentiles)
            colors[p] = cmap((p - min(percentiles)) / spread if spread else 0.5)
        linestyles[p] = standard_linestyles.get(p, "-")

    # The fixed quotient grid, drawn behind the curves.
    for band in bands:
        ax.axhline(band, color="0.6", linewidth=0.8, linestyle=":", zorder=1)
        ax.annotate(
            f"Q={band}", (age_range[1], band), xytext=(4, 0),
            textcoords="offset points", va="center", ha="left",
            fontsize=8, color="0.45", annotation_clip=False,
        )

    for percentile in percentiles:
        values = _centile_curve(equation, sex, height, parameter, ethnicity,
                                ages, stats.norm.ppf(percentile / 100.0))
        ax.plot(
            ages,
            values / denominator,
            label=f"{percentile}th percentile",
            linewidth=2,
            linestyle=linestyles[percentile],
            color=colors[percentile],
            zorder=2,
        )

    param_label = getattr(parameter, "name", str(parameter))
    ax.set_xlabel("Age (years)", fontsize=12)
    ax.set_ylabel(f"{param_label} quotient (measured / {denominator:.2f})", fontsize=12)
    ax.set_ylim(bottom=0)
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)

    if title is None:
        sex_label = "Male" if sex == 1 else "Female"
        title = (f"{equation.__class__.__name__} centiles as "
                 f"{type(quotient).__name__} quotients ({sex_label}, {height} cm)")

    ax.set_title(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    return fig
