from io import BytesIO
import xlsxwriter
from domain import rndDate, getWeekEnds, getMonthEnds, Summary, SummaryFields, Currency, DonationType


WORKBOOKDEFAULTS = {'default_date_format': 'dd/mm/yy'}
WORKBOOKFORMATS = {
        "header": {'bold': True, 'font_color': 'white', 'bg_color': 'red', 'font_size': 13},
        "weekend": {'bold': False, 'font_color': 'white', 'bg_color': 'red', 'font_size': 9, 'num_format': 'dd/mm/yy', 'align': 'center'},
        "month": {'bold': False, 'font_color': 'white', 'bg_color': 'red', 'font_size': 9, 'num_format': 'mmm-yy', 'align': 'center'},
        "total": {'top': 1, 'border_color': 'red'}
    }
COL0WIDTH = 15
COLXWIDTH = 8


def getDonationsReport(store, startDate, endDate):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, WORKBOOKDEFAULTS)
    formats = addFormats(workbook)

    donations = store.getDonations(rndDate(startDate, 'month', 'down'), rndDate(endDate, 'month', 'up'))
    monthEnds = getMonthEnds(startDate, endDate)
    addRevenuesByMonth(workbook, formats, monthEnds, donations)
    addDonationsByMonth(workbook, formats, monthEnds, donations)

    donations = store.getDonations(rndDate(startDate, 'week', 'down'), rndDate(endDate, 'week', 'up'))
    weekEnds = getWeekEnds(startDate, endDate)
    addRevenuesByWeek(workbook, formats, weekEnds, donations)
    addDonationsByWeek(workbook, formats, weekEnds, donations)

    workbook.close()
    output.seek(0)
    return output


def writeCell(ws, row, col, value, format):
    if value is None:
        ws.write_blank(row, col, None, cell_format=format)
    else:
        ws.write(row, col, value, format)
    return col+1


def writeRow(ws, row, cell0Value, cell0format, values, format):
    col = 0
    col = writeCell(ws, row, col, cell0Value, cell0format)
    if isinstance(values, int):
        values = [None]*values

    for value in values:
        col = writeCell(ws, row, col, value, format)
    col = writeCell(ws, row, col, None, cell0format)
    return row+1


def addWorksheet(workbook, title):
    ws = workbook.add_worksheet(title)
    ws.set_column(0, 0, COL0WIDTH)
    ws.freeze_panes(1, 1)  # Freeze the first row.
    return ws


def addRevenuesByMonth(workbook, formats, monthEnds, donations):
    summary = Summary(donations, [SummaryFields.CURRENCY, SummaryFields.MONTH, SummaryFields.TYPE])

    ws = addWorksheet(workbook, 'RevenuesByMonth')
    row = 0

    row = writeRow(ws, row, 'Month', formats['header'], monthEnds, formats['month'])

    for currency in Currency:
        if currency not in summary:
            continue

        row = writeRow(ws, row, currency.name.upper(), formats['header'], len(monthEnds), formats['month'])

        for type in DonationType:
            values = []
            for month in monthEnds:
                try:
                    values.append(summary[currency][month][type].total[currency].amount)
                except KeyError:
                    values.append(None)

            row = writeRow(ws, row, type.name.lower(), formats['header'], values, None)

        values = []
        for month in monthEnds:
            try:
                values.append(summary[currency][month].total[currency].amount)
            except KeyError:
                values.append(None)
        row = writeRow(ws, row, 'Total', formats['header'], values, formats['total'])
    row = writeRow(ws, row, None, formats['header'], len(monthEnds), formats['header'])


def addRevenuesByWeek(workbook, formats, weekEnds, donations):
    summary = Summary(donations, [SummaryFields.CURRENCY, SummaryFields.WEEK, SummaryFields.TYPE])

    ws = addWorksheet(workbook, 'RevenuesByWeek')
    row = 0

    row = writeRow(ws, row, 'Week', formats['header'], weekEnds, formats['weekend'])

    for currency in Currency:
        if currency not in summary:
            continue

        row = writeRow(ws, row, currency.name.upper(), formats['header'], len(weekEnds), formats['weekend'])

        for type in DonationType:
            values = []
            for week in weekEnds:
                try:
                    values.append(summary[currency][week][type].total[currency].amount)
                except KeyError:
                    values.append(None)

            row = writeRow(ws, row, type.name.lower(), formats['header'], values, None)

        values = []
        for week in weekEnds:
            try:
                values.append(summary[currency][week].total[currency].amount)
            except KeyError:
                values.append(None)
        row = writeRow(ws, row, 'Total', formats['header'], values, formats['total'])
    row = writeRow(ws, row, None, formats['header'], len(weekEnds), formats['header'])


def addDonationsByMonth(workbook, formats, monthEnds, donations):
    summary = Summary(donations, [SummaryFields.MONTH, SummaryFields.TYPE])
    ws = addWorksheet(workbook, 'DonationsByMonth')
    row = 0

    row = writeRow(ws, row, 'Month', formats['header'], monthEnds, formats['month'])

    for type in DonationType:
        values = []
        for month in monthEnds:
            try:
                values.append(summary[month][type].total.count)
            except KeyError:
                values.append(None)
        row = writeRow(ws, row, type.name.lower(), formats['header'], values, None)

    values = []
    for month in monthEnds:
        try:
            values.append(summary[month].total.count)
        except KeyError:
            values.append(None)
    row = writeRow(ws, row, 'Total', formats['header'], values, formats['total'])
    row = writeRow(ws, row, None, formats['header'], len(monthEnds), formats['header'])


def addDonationsByWeek(workbook, formats, weekEnds, donations):
    summary = Summary(donations, [SummaryFields.WEEK, SummaryFields.TYPE])
    ws = addWorksheet(workbook, 'DonationsByWeek')
    row = 0

    row = writeRow(ws, row, 'Week', formats['header'], weekEnds, formats['weekend'])

    for type in DonationType:
        values = []
        for week in weekEnds:
            try:
                values.append(summary[week][type].total.count)
            except KeyError:
                values.append(None)
        row = writeRow(ws, row, type.name.lower(), formats['header'], values, None)

    values = []
    for week in weekEnds:
        try:
            values.append(summary[week].total.count)
        except KeyError:
            values.append(None)
    row = writeRow(ws, row, 'Total', formats['header'], values, formats['total'])
    row = writeRow(ws, row, None, formats['header'], len(weekEnds), formats['header'])


def addFormats(workbook):
    return {k: workbook.add_format(v) for (k, v) in WORKBOOKFORMATS.items()}
