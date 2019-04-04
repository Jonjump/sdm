from io import BytesIO, StringIO
from functools import wraps
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file, redirect, session, g
from flask_oidc import OpenIDConnect, MemoryCredentials
from domain import BenefitType, Delivery, Money, Benefit, BenefitException, rndDate, getWeekEnds, Summary, SummaryFields
from domain import PaymentProvider, DonationType
from infrastructure import StoreFactory, StoreConfig, StoreType, StoreDuplicate, TransactionImporterFactory
from reports import getDonationsReport
import config

BASE_URI = f"https://{config.HOST}:{config.PORT}"

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': config.APPSECRETKEY,
    'TESTING': not config.PRODUCTION,
    'DEBUG': not config.PRODUCTION,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': config.PRODUCTION,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_GOOGLE_APPS_DOMAIN': config.OIDC_GOOGLE_APPS_DOMAIN,
    'OVERWRITE_REDIRECT_URI': config.OVERWRITE_REDIRECT_URI
})


@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    return response


oidc = OpenIDConnect(app=app, credentials_store=MemoryCredentials())


logging.basicConfig(level=logging.DEBUG)


def require_login(view_func):
    """
    Use this to decorate view functions that require a user to be logged
    in. If the user is not already logged in, they will be sent to the
    Provider to log in, after which they will be returned.
    """
    @wraps(view_func)
    def decorated(*args, **kwargs):
        if g.oidc_id_token is None:
            return oidc.redirect_to_auth_server(request.url)

        if 'user' not in session:
            session['user_email'] = oidc.user_getfield('email')

        return view_func(*args, **kwargs)

    return decorated


def getStore():
    """create singleton on first call
    """
    if not hasattr(g, 'store'):
        store = StoreFactory(StoreConfig(StoreType.SQLLITE, config.SQLITE3DB))
        g.store = store
    return g.store


@app.teardown_appcontext
def teardownContext(error):
    if hasattr(g, 'store'):
        g.store.close()


@app.route('/benefits/add')
@require_login
def benefitsAdd():
    messages = {}
    return render_template('benefits/benefitForm.html', active='benefits', action="add", form=request.form.to_dict(), deliveryTypes=Delivery,
                           benefitTypes=BenefitType, messages=messages)


@app.route('/benefits/<storeId>/getDonors')
@require_login
def getQualifyingDonors(storeId):
    store = getStore()
    benefit = store.getBenefit(storeId)
    output = BytesIO()
    output.write("Email Address\n".encode("utf8"))
    output.writelines([(donor+'\n').encode("utf8") for donor in store.getQualifyingDonors(benefit)])
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        attachment_filename=benefit.csvFileName,
        mimetype='text/csv',
        cache_timeout=-1
    )


@app.route('/benefits/', methods=['GET'])
@require_login
def getBenefits():
    store = getStore()
    status = request.args.get("status")

    if status == "current":
        return render_template('/benefits/listCurrent.html', active="benefits", benefits=store.getCurrentBenefits())
    elif status == "delivered":
        return render_template('/benefits/listDelivered.html', active="benefits", benefits=store.getDeliveredBenefits())
    else:
        return render_template('/benefits/listPending.html', active="benefits", benefits=store.getPendingBenefits())


@app.route('/benefits/', methods=['POST'])
@require_login
def addBenefit():
    try:
        store = getStore()
        store.addBenefit(getBenefitFromRequest())
    except Exception as e:
        messages = {e.key: e.message}
        return render_template('benefits/benefitForm.html', active='benefits', action="add", form=request.form.to_dict(), deliveryTypes=Delivery,
                               benefitTypes=BenefitType, messages=messages)
    return redirect("/benefits", code=303)  # 303 changes the request type to a GET


@app.route('/benefits/<storeId>', methods=['GET'])
@require_login
def getBenefit(storeId):
    store = getStore()
    benefit = store.getBenefit(storeId)
    form = toForm(benefit)
    return render_template('benefits/benefitForm.html', active='benefits', action="save", form=form, deliveryTypes=Delivery,
                           benefitTypes=BenefitType, messages={})


@app.route('/benefits/<storeId>', methods=['DELETE'])
@require_login
def deleteBenefit(storeId):
    store = getStore()
    store.deleteBenefit(storeId)
    return redirect("/benefits", code=303)  # 303 changes the request type to a GET


@app.route('/benefits/<storeId>', methods=['POST'])
@require_login
def updateBenefit(storeId):
    try:
        store = getStore()
        benefit = getBenefitFromRequest()
        store.updateBenefit(benefit)
    except BenefitException as e:
        messages = {e.key: e.message}
        return render_template('benefits/benefitForm.html', active='benefits', action="save", form=request.form.to_dict(), deliveryTypes=Delivery,
                               benefitTypes=BenefitType, messages=messages)
    return redirect("/benefits", code=303)  # 303 changes the request type to a GET


@app.route('/donations/upload', methods=['GET', 'POST'])
@require_login
def donationsUpload():
    if request.method == 'GET':
        paymentProvider = request.args["paymentProvider"]
        return render_template('donations/upload.html', active="donations", paymentProvider=paymentProvider)

    try:
        store = getStore()
        paymentProvider = PaymentProvider[request.form["paymentProvider"]]
        file = request.files['file']
        checkFileAllowed(file.filename)
        # bug in spooledTemporaryFile - AttributeError: 'SpooledTemporaryFile' object has no attribute 'readable'
        # textWrapper=io.TextIOWrapper(file.stream,encoding='utf-8',write_through=True)
        # workaround
        textWrapper = StringIO(file.read().decode("latin-1"))

        donations = []
        importer = TransactionImporterFactory(paymentProvider, textWrapper)

        dupes = []
        added = []
        for donation in importer:
            donations.append(donation)
            try:
                store.insertDonation(donation)
                added.append(donation)
            except StoreDuplicate:
                dupes.append(donation)

        return render_template('donations/uploadResult.html', active="donations", filename=file.filename, added=added, badRows=importer.badRows, dupes=dupes)
    except Exception as e:
        raise e
        return donationsByWeek()


@app.route('/donations/<item>')
@app.route('/donations/index')
@app.route('/donations')
@require_login
def donationsByWeek(item='byWeek'):
    store = getStore()
    today = datetime.now().date()
    endDate = rndDate(today, "week", "up") - timedelta(days=7)
    startDate = endDate - timedelta(days=(52*7)-1)
    weekEnds = getWeekEnds(startDate, endDate)
    donations = store.getDonations(startDate, endDate)
    summary = Summary(donations, [SummaryFields.SOURCE, SummaryFields.WEEK, SummaryFields.TYPE])
    return render_template('donations/'+item+'.html', active="donations", weekEnds=weekEnds, summary=summary, sources=PaymentProvider, types=DonationType)


# @app.route('/file/<item>')
# @app.route('/file')
# @require_login
# def file(item='index'):
#     return render_template('file/'+item+'.html', active="file")


@app.route('/reports/download')
@require_login
def reportsDownload():
    store = getStore()
    args = request.args
    startDate = fromHtmlDate(args['startDate'])
    endDate = fromHtmlDate(args['endDate'])

    return send_file(
        getDonationsReport(store, startDate, endDate),
        as_attachment=True,
        attachment_filename='donationsReport.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/reports')
@require_login
def reports():
    form = {
        "startDate": toHtmlDate(datetime.now()-timedelta(days=365)),
        "endDate": toHtmlDate(datetime.now())
    }
    return render_template('reports.html', active="reports", form=form)


@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html', active="help")


@app.route('/logout')
def logout():
    if 'user_email' in session:
        session.pop('user_email')
    oidc.logout()
    return home()


HTMLDATEFORMAT = "%Y-%m-%d"


def toHtmlDate(date):
    return date.strftime(HTMLDATEFORMAT)


def fromHtmlDate(s):
    return datetime.strptime(s, HTMLDATEFORMAT).date()


def toForm(benefit):
    result = {
        "storeId": benefit._storeId,
        "reward": benefit.reward,
        "type": benefit.type.value,
        "delivery": benefit.delivery.value,
        "startDate": toHtmlDate(benefit.startDate),
        "endDate": toHtmlDate(benefit.endDate),
        "minAmount": str(benefit.minAmount),
        "status": benefit.status.name
    }
    if benefit.completed:
        result["completed"] = "on"
    return result


def getBenefitFromRequest():
    form = request.form
    if form["storeId"]:
        storeId = form["storeId"]
    else:
        storeId = None

    delivery = Delivery(int(form["delivery"]))
    startDate = fromHtmlDate(form["startDate"])
    endDate = fromHtmlDate(form["endDate"])
    completed = "completed" in form and form["completed"] == "on"

    type = BenefitType(form["type"])
    reward = form["reward-"+form["type"]]
    try:
        minAmount = Money.fromString(form["minAmount-"+form["type"]])
    except:  # noqa: E722
        minAmount = None

    return Benefit.Factory(storeId, type, reward, startDate, endDate, delivery, minAmount, completed)


def checkFileAllowed(filename):
    if '.' not in filename:
        raise Exception("no . in filename")
    if filename.rsplit('.', 1)[1].lower() != "csv":
        raise Exception("extension must be csv")
