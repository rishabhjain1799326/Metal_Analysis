def analyze_gold_impact(indicator, current, previous):
    """
    Determine the general directional impact of a macro
    indicator on gold based on its movement.

    Returns a structured analysis.
    """

    change = current - previous

    if change == 0:
        direction = "UNCHANGED"
    elif change > 0:
        direction = "INCREASED"
    else:
        direction = "DECREASED"

    # Fed Funds Rate
    if indicator == "fed_funds_rate":

        if change > 0:
            impact = "HEADWIND"
            reason = (
                "Higher interest rates can increase the opportunity "
                "cost of holding non-yielding gold."
            )

        elif change < 0:
            impact = "SUPPORTIVE"
            reason = (
                "Lower interest rates can reduce the opportunity "
                "cost of holding non-yielding gold."
            )

        else:
            impact = "NEUTRAL"
            reason = "The policy rate is unchanged."

    # CPI
    elif indicator == "cpi":

        if change > 0:
            impact = "HEADWIND"
            reason = (
                "Higher inflation can reduce expectations for "
                "near-term monetary easing and may contribute to "
                "higher interest rates."
            )

        elif change < 0:
            impact = "SUPPORTIVE"
            reason = (
                "Lower inflation can increase expectations for "
                "monetary easing, which can support gold."
            )

        else:
            impact = "NEUTRAL"
            reason = "Inflation is unchanged on the measured basis."

    # PCE
    elif indicator == "pce":

        if change > 0:
            impact = "HEADWIND"
            reason = (
                "Higher PCE inflation can reinforce expectations "
                "for tighter monetary policy."
            )

        elif change < 0:
            impact = "SUPPORTIVE"
            reason = (
                "Lower PCE inflation can support expectations "
                "for easier monetary policy."
            )

        else:
            impact = "NEUTRAL"
            reason = "PCE inflation is unchanged on the measured basis."

    # Unemployment
    elif indicator == "unemployment":

        if change > 0:
            impact = "SUPPORTIVE"
            reason = (
                "Rising unemployment can indicate labor-market "
                "weakness and potentially increase expectations "
                "for monetary easing."
            )

        elif change < 0:
            impact = "HEADWIND"
            reason = (
                "Falling unemployment can indicate a stronger "
                "labor market and potentially reduce expectations "
                "for monetary easing."
            )

        else:
            impact = "NEUTRAL"
            reason = "The unemployment rate is unchanged."

    # 10Y Treasury
    elif indicator == "treasury_10y":

        if change > 0:
            impact = "HEADWIND"
            reason = (
                "Higher Treasury yields can increase the "
                "opportunity cost of holding non-yielding gold."
            )

        elif change < 0:
            impact = "SUPPORTIVE"
            reason = (
                "Lower Treasury yields can reduce the "
                "opportunity cost of holding gold."
            )

        else:
            impact = "NEUTRAL"
            reason = "The 10Y Treasury yield is unchanged."

    # 10Y Real Yield
    elif indicator == "real_yield_10y":

        if change > 0:
            impact = "HEADWIND"
            reason = (
                "Higher real yields generally increase the "
                "opportunity cost of holding non-yielding gold."
            )

        elif change < 0:
            impact = "SUPPORTIVE"
            reason = (
                "Lower real yields generally reduce the "
                "opportunity cost of holding gold."
            )

        else:
            impact = "NEUTRAL"
            reason = "The 10Y real yield is unchanged."

    else:
        impact = "UNKNOWN"
        reason = "No gold-impact rule has been defined."

    return {
        "indicator": indicator,
        "current": current,
        "previous": previous,
        "change": change,
        "direction": direction,
        "impact": impact,
        "reason": reason
    }