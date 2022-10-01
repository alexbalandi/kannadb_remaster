def YearDifferenceRounded(date, epoch):
    year_diff_base = date.year - epoch.year - 1

    if date.month > epoch.month:
        year_diff_base += 1
    elif date.month == epoch.month and date.day >= epoch.day:
        year_diff_base += 1

    return year_diff_base
