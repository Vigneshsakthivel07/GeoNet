def validate_parcel(
    deviations,
    overlap_percentage,
    points_outside,
    tolerance,
    minimum_overlap
):
    """
    Validate a parcel using spatial measurements.

    Parameters
    ----------
    deviations : dict
        Boundary deviation for each point.

    overlap_percentage : float
        Percentage of polygon overlap.

    points_outside : int
        Number of modern survey points
        outside the transformed FMB parcel.

    tolerance : float
        Maximum allowed deviation in metres.

    minimum_overlap : float
        Minimum required polygon overlap percentage.
    """

    maximum_deviation = max(
        deviations.values()
    )

    average_deviation = (
        sum(deviations.values())
        / len(deviations)
    )

    deviation_ok = (
        maximum_deviation <= tolerance
    )

    overlap_ok = (
        overlap_percentage >= minimum_overlap
    )

    points_ok = (
        points_outside == 0
    )

    if (
        deviation_ok
        and overlap_ok
        and points_ok
    ):
        status = "VERIFIED"
    else:
        status = "MISMATCH"

    return {
        "status": status,
        "maximum_deviation": maximum_deviation,
        "average_deviation": average_deviation,
        "overlap_percentage": overlap_percentage,
        "points_outside": points_outside,
        "deviation_ok": deviation_ok,
        "overlap_ok": overlap_ok,
        "points_ok": points_ok
    }
