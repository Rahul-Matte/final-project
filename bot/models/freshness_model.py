def check_freshness(image, days):
    """
    Checks the freshness of the crop based on days since harvest.
    'image' parameter is kept for future cv-based freshness analysis compatibility.
    """
    
    if days < 2:
        return "Very Fresh"

    elif days < 5:
        return "Fresh"

    else:
        return "Not Fresh"
