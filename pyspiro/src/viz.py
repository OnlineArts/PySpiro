"""
Visualization utilities for lung function reference equations.

Provides functions for generating centile (percentile) curves that illustrate
reference populations across age ranges.
"""

import numpy as np
import pandas as pd


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
    import matplotlib.cm as cm
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
        z = z_scores[percentile]
        values = []

        for age in ages:
            try:
                if ethnicity is not None:
                    l, m, s = equation.lms(sex, age, height, ethnicity, parameter, 0)
                else:
                    l, m, s = equation.lms(sex, age, height, parameter, 0)
            except TypeError:
                l, m, s = equation.lms(sex, age, height, parameter, 0)

            if pd.isna(l) or pd.isna(m) or pd.isna(s):
                values.append(np.nan)
            else:
                if l != 0:
                    value = m * ((1 + z * l * s) ** (1 / l))
                else:
                    value = m * np.exp(z * s)
                values.append(value)

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
