from datetime import date, timedelta


def getMonthStart(d):
    return date(d.year, d.month, 1)


def getMonthEnd(d):
    year = d.year
    month = d.month+1
    if d.month == 12:
        year = d.year+1
        month = 1
    else:
        year = d.year
        month = d.month+1

    return date(year, month, 1) - timedelta(days=1)


def getWeekStart(d):
    return d - timedelta(days=d.weekday())


def getWeekEnd(d):
    return d + timedelta(days=6-d.weekday())


lookup = {
    "month": {
        "up": getMonthEnd,
        "down": getMonthStart
    },
    "week": {
        "up": getWeekEnd,
        "down": getWeekStart
    }
}


def rndDate(d, unit, direction):
    if not isinstance(d, date):
        d = d.date()
    unit = unit.strip().lower()
    direction = direction.strip().lower()
    fn = lookup[unit][direction]
    return fn(d)


def getWeekEnds(startDate, endDate):
    startDate = rndDate(startDate, 'week', 'up')
    endDate = rndDate(endDate, 'week', 'up')
    return [startDate + timedelta(days=i) for i in range(0, (endDate-startDate).days+1, 7)]


def getMonthEnds(startDate, endDate):
    startDate = rndDate(startDate, 'month', 'up')
    endDate = rndDate(endDate, 'month', 'up')
    startMonth = 12 * startDate.year + startDate.month
    endMonth = 12 * endDate.year + endDate.month
    return [rndDate(date(year=int(i/12), month=(i % 12) + 1, day=1), 'month', 'up') for i in range(startMonth-1, endMonth, 1)]
