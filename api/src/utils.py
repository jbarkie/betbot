def format_american_odds(decimal_odds):
    if decimal_odds == 1:
        return "None"
    elif decimal_odds > 2:
        underdog_odds = round(100 * (decimal_odds - 1))
        return f"+{underdog_odds}"
    else:
        favorite_odds = round(100 / (decimal_odds - 1))
        return f"-{favorite_odds}"
