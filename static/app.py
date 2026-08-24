from datetime import datetime
import os
from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ustaz_research_pro.db"
app.config["SECRET_KEY"] = "ustaz_research_secure_key"

UPLOAD_FOLDER = "static/uploads"
PDF_STORAGE_FOLDER = "static/pdf_storage"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PDF_STORAGE_FOLDER"] = PDF_STORAGE_FOLDER

db = SQLAlchemy(app)

# --- ДЕРЕКТЕР БАЗАСЫНЫҢ МОДЕЛЬДЕРІ ---


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    profile_pic = db.Column(
        db.String(200), nullable=True, default="default_avatar.png"
    )
    bonuses = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default="teacher")
    researches = db.relationship(
        "Research", backref="teacher", lazy=True, cascade="all, delete-orphan"
    )


class Research(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    skill = db.Column(db.String(50), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    problem = db.Column(db.Text, nullable=False)
    selected_title = db.Column(db.Text, nullable=False)

    relevance = db.Column(db.Text, nullable=True)
    goal = db.Column(db.Text, nullable=True)
    tasks = db.Column(db.Text, nullable=True)
    hypothesis = db.Column(db.Text, nullable=True)
    expected_result = db.Column(db.Text, nullable=True)
    apparatus_approved = db.Column(db.Boolean, default=False)
    apparatus_score = db.Column(db.Integer, default=0)
    apparatus_feedback = db.Column(db.Text, nullable=True, default="Тексерілмеді")

    lit_review = db.Column(db.Text, nullable=True)
    lit_approved = db.Column(db.Boolean, default=False)
    lit_score = db.Column(db.Integer, default=0)
    lit_feedback = db.Column(db.Text, nullable=True, default="Тексерілмеді")

    experiment_analysis = db.Column(db.Text, nullable=True)
    exp_approved = db.Column(db.Boolean, default=False)
    exp_score = db.Column(db.Integer, default=0)
    exp_feedback = db.Column(db.Text, nullable=True, default="Тексерілмеді")

    survey_data = db.Column(db.Text, nullable=True)
    survey_approved = db.Column(db.Boolean, default=False)
    survey_score = db.Column(db.Integer, default=0)
    survey_feedback = db.Column(db.Text, nullable=True, default="Тексерілмеді")

    references_list = db.Column(db.Text, nullable=True)
    refs_approved = db.Column(db.Boolean, default=False)
    refs_score = db.Column(db.Integer, default=0)
    refs_feedback = db.Column(db.Text, nullable=True, default="Тексерілмеді")

    admin_feedback = db.Column(
        db.Text, nullable=True, default="Әзірге жалпы кері байланыс жоқ"
    )
    status = db.Column(db.String(50), default="Жеке кабинетте сақталды")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CalendarTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    task_name = db.Column(db.String(200), nullable=False)
    task_date = db.Column(db.String(50), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    sender = db.Column(db.String(20), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    admin_reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher = db.relationship("User", backref="messages")


class SharedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(PDF_STORAGE_FOLDER):
        os.makedirs(PDF_STORAGE_FOLDER)

    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            password="admin123",
            full_name="Бас Әкімші",
            category="Педагог-шебер",
            role="admin",
        )
        db.session.add(admin_user)
        db.session.commit()

# --- ПӘНДЕР МЕН ДЕРЕКТЕР БАЗАСЫ (Source: 1, 2, 3) ---
PLATFORM_DATA = {
    "pander": [
        "Бастауыш сынып",
        "Қазақ тілі",
        "Қазақ әдебиеті",
        "Ағылшын тілі",
        "Математика",
        "Физика",
        "Химия",
        "Биология",
        "География",
        "Тарих",
        "Информатика",
        "STEAM",
    ],
    "kategoriya": [
        "Педагог",
        "Педагог-модератор",
        "Педагог-сарапшы",
        "Педагог-зерттеуші",
        "Педагог-шебер",
    ],
    "synyp": ["1–4 сынып", "5–6 сынып", "7–9 сынып", "10–11 сынып"],
    "dagdy": [
        "Функционалдық сауаттылық",
        "Сыни ойлау",
        "Зерттеушілік дағды",
        "Шығармашылық ойлау",
        "Коммуникативтік дағды",
        "Цифрлық сауаттылық",
        "Проблеманы шешу",
        "Дәлелдеу және аргументация",
        "Ақпаратты талдау",
        "Модельдеу",
        "Ынтымақтастық",
        "Өзіндік оқу",
        "Рефлексия",
        "Медиасауаттылық",
        "Ақпараттық сауаттылық",
        "Математикалық сауаттылық",
    ],
    "adister": [
        "Жобалық оқыту",
        "Зерттеушілік оқыту",
        "Проблемалық оқыту",
        "STEAM тәсілі",
        "Жасанды интеллект құралдары",
        "Ойын технологиясы",
        "Саралап оқыту",
        "Flipped Classroom",
        "Цифрлық оқыту",
    ],
    "problemalar": {
        "Бастауыш сынып": [
            "оқу жылдамдығы",
            "мәтіннің негізгі ойын анықтау",
            "мәтіннен нақты ақпаратты табу",
            "оқиғаларды ретімен орналастыру",
            "оқығанын өз сөзімен мазмұндау",
            "мәтін бойынша сұрақ құрастыру",
            "сөздік қорды белсенді қолдану",
            "сөйлемді дұрыс құрау",
            "өз ойын ауызша жүйелі жеткізу",
            "жазба жұмысын жоспарлау",
            "мәтінді жалғастырып жазу",
            "көрнекілікпен жұмыс",
            "математикалық терминдерді түсіну",
            "мәтіндік есептің шартын талдау",
            "есепті өмірлік жағдаймен байланыстыру",
            "амал таңдау стратегиясы",
            "өлшем бірліктерін қолдану",
            "кесте мен диаграмманы оқу",
            "заңдылықты анықтау",
            "логикалық есептерді шешу",
            "өз оқуын жоспарлау",
            "тапсырманы соңына дейін орындау",
            "өз жұмысын бағалау",
            "қатесін тауып түзету",
            "топта жұмыс істеу",
            "цифрлық құралды қолдану",
            "ақпаратты салыстыру",
            "шығармашылық идея ұсыну",
            "рефлексия жасау",
            "дәлел келтіру",
        ],
        "Қазақ тілі": [
            "мәтіннің негізгі ақпаратын анықтау",
            "мәтін құрылымын талдау",
            "ақпаратты іріктеу",
            "мәтіндерді салыстыру",
            "мәтін мазмұнын интерпретациялау",
            "сөз мағынасын контексте анықтау",
            "лексикалық бірліктерді қолдану",
            "терминдерді дұрыс қолдану",
            "грамматикалық норманы сақтау",
            "сөйлем құрылымын түрлендіру",
            "пунктуациялық норманы қолдану",
            "орфографиялық сауаттылық",
            "функционалдық мәтін құрастыру",
            "ресми мәтін жазу",
            "аргументативті мәтін жазу",
            "пікірді дәлелдеу",
            "ауызша ойды жүйелеу",
            "пікірталаста жауап беру",
            "ақпаратты жинақтау",
            "дерек пен пікірді ажырату",
            "медиамәтінді талдау",
            "сыни оқылым",
            "қорытынды жасау",
            "себеп-салдарды анықтау",
            "сұрақ қою сапасы",
            "зерттеу нәтижесін ұсыну",
            "цифрлық мәтінмен жұмыс",
            "өз жазбасын редакциялау",
            "рефлексия",
            "функционалдық сауаттылық",
        ],
        "Қазақ әдебиеті": [
            "сюжеттік құрылымды талдау",
            "кейіпкер бейнесін ашу",
            "кейіпкер әрекетіне баға беру",
            "авторлық позицияны анықтау",
            "тақырып пен идеяны ажырату",
            "көркем детальды талдау",
            "образдар жүйесін түсіндіру",
            "композицияны талдау",
            "көркемдегіш құралдарды анықтау",
            "метафора мен символды интерпретациялау",
            "мәтіннен дәлел келтіру",
            "дәйексөзді орынды қолдану",
            "әдеби пікір қалыптастыру",
            "пікірді дәлелдеу",
            "шығармаларды салыстыру",
            "жанрларды ажырату",
            "әдеби контексті түсіну",
            "тарихи контексті байланыстыру",
            "ұлттық құндылықтарды талдау",
            "кейіпкер таңдауының салдарын бағалау",
            "оқиғаны қазіргі өмірмен байланыстыру",
            "шығармашылық интерпретация",
            "балама финал ұсыну",
            "әдеби эссе жазу",
            "сыни оқылым",
            "пікірталас жүргізу",
            "оқырман рефлексиясы",
            "цифрлық әдеби ресурспен жұмыс",
            "мәтінді визуалдау",
            "зерттеу нәтижесін ұсыну",
        ],
        "Ағылшын тілі": [
            "ауызша қарым-қатынас дағдысы",
            "мәтінді оқып түсіну",
            "тыңдалым арқылы ақпаратты қабылдау",
            "лексикалық қорды қолдану",
            "грамматикалық құрылымдарды сақтау",
        ],
        "Математика": [
            "мәтіндік есепті талдау",
            "есеп шартын математикалық модельге айналдыру",
            "шешу стратегиясын таңдау",
            "бірнеше шешім тәсілін салыстыру",
            "математикалық дәлелдеу",
            "логикалық пайымдау",
            "өрнекті түрлендіру",
            "теңдеу құру",
            "теңсіздікті шешу",
            "функция графигін интерпретациялау",
            "график құру",
            "кестелік деректі талдау",
            "диаграмманы түсіндіру",
            "статистикалық деректі бағалау",
            "ықтималдықты қолдану",
            "пропорцияны қолдану",
            "пайызды есептерде пайдалану",
            "өлшем бірліктерін түрлендіру",
            "геометриялық модель құру",
            "кеңістіктік ойлау",
            "формуланы таңдау",
            "есеп нәтижесін бағалау",
            "жуық мәнді түсіндіру",
            "қате шешімді талдау",
            "математикалық тіл қолдану",
            "цифрлық құралды пайдалану",
            "зерттеу дерегін сандық талдау",
            "математикалық сауаттылық",
            "проблеманы шешу",
            "рефлексия",
        ],
        "Физика": [
            "физикалық ақпаратты талдау",
            "физикалық шамаларды дұрыс қолдану",
            "физикалық шамалардың өлшем бірліктерін қолдану",
            "формуланы таңдау және қолдану",
            "физикалық есептің шартын талдау",
            "есепті математикалық модельге айналдыру",
            "есеп шығару стратегиясын таңдау",
            "графикті оқу және интерпретациялау",
            "физикалық график құру",
            "кестелік деректерді талдау",
            "физикалық құбылыстарды бақылау",
            "физикалық құбылыстардың себеп-салдарын түсіндіру",
            "механикалық қозғалысты талдау",
            "жылдамдық пен үдеуді анықтау",
            "күштердің әсерін түсіндіру",
            "Ньютон заңдарын қолдану",
            "энергияның түрленуін түсіндіру",
            "жұмыс пен қуатты есептеу",
            "қысым және оның қолданылуын түсіндіру",
            "жылу құбылыстарын талдау",
            "жылу берілу түрлерін ажырату",
            "электр тізбегін құрастыру және талдау",
            "электр шамаларын есептеу",
            "Ом заңын қолдану",
            "магниттік құбылыстарды түсіндіру",
            "жарық құбылыстарын зерттеу",
            "оптикалық құбылыстарды түсіндіру",
            "зерттеу сұрағын құрастыру",
            "экспериментті жоспарлау",
            "эксперимент нәтижесін талдау",
        ],
        "Химия": [
            "химиялық ақпаратты талдау",
            "химиялық терминдерді дұрыс қолдану",
            "химиялық формулаларды оқу және құрастыру",
            "химиялық теңдеулерді құрастыру",
            "химиялық реакцияларды теңестіру",
            "химиялық реакция түрлерін ажырату",
            "реакция белгілерін анықтау",
            "заттардың қасиеттерін салыстыру",
            "заттардың агрегаттық күйлерін түсіндіру",
            "атом құрылысының моделін түсіндіру",
            "периодтық жүйемен жұмыс істеу",
            "химиялық элементтердің периодтық заңдылығын анықтау",
            "элементтердің қасиеттерін периодтық жүйе арқылы болжау",
            "химиялық байланыс түрлерін ажырату",
            "молекулалық және иондық құрылымды түсіндіру",
            "валенттілікті анықтау",
            "тотығу дәрежесін анықтау",
            "зат мөлшерін есептеу",
            "молярлық массаны есептеу",
            "мольдік көлемді қолдану",
            "химиялық есептерді шешу",
            "ерітінді концентрациясын есептеу",
            "ерітінді дайындау есептерін шешу",
            "реакция өнімдерін болжау",
            "химиялық реакцияның себеп-салдарын түсіндіру",
            "зертханалық тәжірибені жоспарлау",
            "эксперимент нәтижесін талдау",
            "гипотеза ұсыну және тексеру",
            "зертханалық қауіпсіздік ережелерін сақтау",
            "химиялық деректерді кесте және график арқылы талдау",
        ],
        "Биология": [
            "биологиялық деректі талдау",
            "график пен кестені интерпретациялау",
            "эксперимент нәтижесін түсіндіру",
            "зерттеу сұрағын құрастыру",
            "гипотеза ұсыну",
            "гипотезаны дәлелдермен тексеру",
            "айнымалыларды анықтау",
            "экспериментті жоспарлау",
            "зертханалық қауіпсіздікті сақтау",
            "микроскоптық бақылау нәтижесін талдау",
            "биологиялық модель құру",
            "құрылым мен қызмет байланысын түсіндіру",
            "себеп-салдарлық байланысты анықтау",
            "эволюциялық дәлелдерді талдау",
            "генетикалық есептерді шешу",
            "экологиялық деректерді бағалау",
            "экологиялық проблеманы ғылыми бағалау",
            "биоалуантүрлілікті талдау",
            "денсаулық деректерін түсіндіру",
            "ғылыми мәтіннен дәлел табу",
            "дәлел мен болжамды ажырату",
            "қорытынды жасау",
            "зерттеу нәтижесін визуалдау",
            "цифрлық симуляцияны пайдалану",
            "AI құралымен деректі талдау",
            "ғылыми аргументация",
            "пәндік терминдерді дәл қолдану",
            "функционалдық биологиялық сауаттылық",
            "зерттеу рефлексиясы",
            "ғылыми коммуникация",
        ],
        "География": [
            "географиялық картаны оқу",
            "картамен жұмыс істеу",
            "шартты белгілерді түсіну және қолдану",
            "географиялық координаталарды анықтау",
            "нысанның географиялық орнын сипаттау",
            "масштабты қолдану",
            "қашықтықты карта бойынша анықтау",
            "физикалық картаны интерпретациялау",
            "тақырыптық картаны талдау",
            "картографиялық деректерді салыстыру",
            "климаттық графикті оқу",
            "ауа райы деректерін талдау",
            "климаттық көрсеткіштер арасындағы байланысты анықтау",
            "табиғи үдерістердің себеп-салдарын түсіндіру",
            "географиялық нысандарды салыстыру",
            "географиялық деректерді кесте және диаграмма арқылы талдау",
            "статистикалық географиялық ақпаратты интерпретациялау",
            "халық саны мен демографиялық көрсеткіштерді талдау",
            "табиғи ресурстардың таралуын бағалау",
            "табиғи ресурстарды тиімді пайдалану жолдарын ұсыну",
            "экологиялық проблеманың себептерін анықтау",
            "экологиялық проблеманың салдарын бағалау",
            "табиғи және антропогендік факторларды ажырату",
            "географиялық заңдылықтарды анықтау",
            "географиялық деректер негізінде болжам жасау",
            "зерттеу сұрағын құрастыру",
            "географиялық зерттеу жоспарын құру",
            "далалық зерттеу нәтижелерін талдау",
            "цифрлық карталар мен GIS құралдарын қолдану",
            "географиялық ақпаратты өмірлік жағдайларда қолдану",
        ],
        "Тарих": [
            "тарихи дерекпен жұмыс істеу",
            "тарихи деректің негізгі ақпаратын анықтау",
            "тарихи оқиғаларды хронологиялық ретпен орналастыру",
            "тарихи даталар мен кезеңдерді сәйкестендіру",
            "тарихи тұлғаның рөлін бағалау",
            "тарихи тұлғаның қызметін тарихи контекстпен байланыстыру",
            "тарихи оқиғаның себептерін анықтау",
            "тарихи оқиғаның салдарын анықтау",
            "себеп-салдарлық байланысты түсіндіру",
            "тарихи оқиғаларды салыстыру",
            "тарихи кезеңдердің ерекшеліктерін анықтау",
            "тарихи үдерістердің сабақтастығын түсіндіру",
            "тарихи картамен жұмыс істеу",
            "тарихи аумақтық өзгерістерді картадан анықтау",
            "тарихи карталарды салыстыру",
            "тарихи статистикалық деректерді талдау",
            "кесте мен диаграммадағы тарихи ақпаратты интерпретациялау",
            "тарихи дерек пен авторлық пікірді ажырату",
            "бірнеше тарихи деректі салыстыру",
            "тарихи деректің сенімділігін бағалау",
            "тарихи оқиғаға қатысты дәлелдерді анықтау",
            "тарихи тұжырымды деректермен дәлелдеу",
            "тарихи пікірді аргументтеу",
            "тарихи мәселе бойынша қорытынды жасау",
            "тарихи оқиғаны қазіргі жағдаймен байланыстыру",
            "тарихи оқиғаның қазіргі қоғамға ықпалын бағалау",
            "ұлттық құндылықтардың тарихи негіздерін түсіндіру",
            "тарихи-мәдени мұраны бағалау",
            "тарихи зерттеу сұрағын құрастыру",
            "тарихи зерттеу нәтижесін ұсыну",
        ],
        "Информатика": [
            "ақпаратты іздеу және іріктеу",
            "ақпараттың сенімділігін бағалау",
            "ақпаратты құрылымдау",
            "ақпаратты кодтау және декодтау",
            "алгоритмді түсіну",
            "алгоритмді құрастыру",
            "алгоритмнің қадамдарын ретімен орындау",
            "блок-схема құру",
            "алгоритмдегі қателерді анықтау",
            "программалау тілінің негізгі құрылымдарын қолдану",
            "айнымалы ұғымын түсіну және қолдану",
            "шартты операторларды қолдану",
            "циклдік құрылымдарды қолдану",
            "функцияларды қолдану",
            "кодты талдау",
            "кодтағы қатені анықтау және түзету",
            "есепті алгоритмдік модельге айналдыру",
            "проблеманы кезең-кезеңімен шешу",
            "деректерді кесте арқылы өңдеу",
            "формулаларды электрондық кестеде қолдану",
            "диаграмма мен график құру",
            "деректерді визуалдау және интерпретациялау",
            "деректер базасымен жұмыс істеу",
            "цифрлық ақпаратты ұйымдастыру",
            "компьютерлік желілердің жұмысын түсіну",
            "киберқауіпсіздік ережелерін қолдану",
            "цифрлық қауіпсіздікті сақтау",
            "жасанды интеллект құралдарын тиімді пайдалану",
            "цифрлық технологияларды өмірлік мәселелерді шешуде қолдану",
        ],
        "STEAM": [
            "ғылыми мәселені анықтау",
            "зерттеу сұрағын құрастыру",
            "зерттеу мақсатын анықтау",
            "гипотеза ұсыну",
            "гипотезаны дәлелдер арқылы тексеру",
            "зерттеу жоспарын құру",
            "инженерлік мәселені анықтау",
            "жобалау шешімін ұсыну",
            "прототип құрастыру",
            "модель жасау",
            "модельді сынақтан өткізу",
            "прототип нәтижесін бағалау",
            "қателерді анықтау және жетілдіру",
            "ғылыми деректерді жинау",
            "деректерді кесте арқылы өңдеу",
            "деректерді график және диаграмма арқылы көрсету",
            "математикалық есептеулерді жобада қолдану",
            "өлшем бірліктерін дұрыс қолдану",
            "технологиялық құралдарды тиімді пайдалану",
            "цифрлық карталар мен модельдеу",
            "бағдарламалау элементтерін жобада қолдану",
            "жасанды интеллект құралдарын зерттеуде пайдалану",
            "ақпаратты сыни бағалау",
            "бірнеше дереккөздегі ақпаратты салыстыру",
            "пәнаралық байланысты анықтау",
            "ғылым мен технологияның байланысын түсіндіру",
            "өнер және дизайн элементтерін қолдану",
            "шығармашылық шешім ұсыну",
            "топтық жобада рөлдерді тиімді орындау",
            "жобаның нәтижесін ғылыми негізде қорғау",
        ],
    },
}

# --- МАРШРУТТАР ---


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(
            username=username, password=password
        ).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session["full_name"] = user.full_name
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("teacher_cabinet"))
        else:
            flash("Қате логин немесе пароль!", "danger")
    return render_template_string(LOGIN_HTML)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        full_name = request.form.get("full_name")
        category = request.form.get("category")

        profile_pic_filename = "default_avatar.png"
        if "profile_pic" in request.files:
            file = request.files["profile_pic"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                unique_name = (
                    f"user_{username}_{int(datetime.now().timestamp())}_{filename}"
                )
                file.save(
                    os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                )
                profile_pic_filename = unique_name

        if User.query.filter_by(username=username).first():
            flash("Бұл логин бос емес!", "danger")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            password=password,
            full_name=full_name,
            category=category,
            profile_pic=profile_pic_filename,
            role="teacher",
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Тіркелу сәтті аяқталды!", "success")
        return redirect(url_for("login"))
    return render_template_string(REGISTER_HTML, data=PLATFORM_DATA)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def teacher_cabinet():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))

    teacher = User.query.get(session["user_id"])
    if not teacher:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action_type")

        if action == "add_task":
            t_name = request.form.get("task_name")
            t_date = request.form.get("task_date")
            if t_name and t_date:
                new_task = CalendarTask(
                    teacher_id=teacher.id, task_name=t_name, task_date=t_date
                )
                db.session.add(new_task)
                db.session.commit()
                flash("Жоспарға жаңа тапсырма қосылды!", "success")

        elif action == "save_research":
            subject = request.form.get("subject")
            grade = request.form.get("grade")
            skill = request.form.get("skill")
            method = request.form.get("method")
            problem = request.form.get("problem")
            selected_title = request.form.get("selected_title")

            new_research = Research(
                teacher_id=teacher.id,
                subject=subject,
                grade=grade,
                skill=skill,
                method=method,
                problem=problem,
                selected_title=selected_title,
                status="Жеке кабинетте сақталды",
            )
            db.session.add(new_research)
            db.session.commit()
            flash("Зерттеу тақырыбы сақталды!", "success")

        return redirect(url_for("teacher_cabinet"))

    all_teachers = User.query.filter_by(role="teacher").order_by(
        User.bonuses.desc()
    ).all()
    teacher_rank = 0
    for idx, t in enumerate(all_teachers, 1):
        if t.id == teacher.id:
            teacher_rank = idx
            break

    my_researches = Research.query.filter_by(teacher_id=teacher.id).all()
    my_tasks = CalendarTask.query.filter_by(teacher_id=teacher.id).all()
    shared_docs = SharedDocument.query.order_by(
        SharedDocument.uploaded_at.desc()
    ).all()
    teacher_messages = Message.query.filter_by(teacher_id=teacher.id).order_by(Message.created_at.asc()).all()

    return render_template_string(
        TEACHER_HTML,
        teacher=teacher,
        teacher_rank=teacher_rank,
        data=PLATFORM_DATA,
        researches=my_researches,
        my_tasks=my_tasks,
        shared_docs=shared_docs,
        teacher_messages=teacher_messages,
    )


@app.route("/toggle_task/<int:task_id>")
def toggle_task(task_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
    task = CalendarTask.query.get_or_404(task_id)
    if task.teacher_id == session["user_id"]:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(url_for("teacher_cabinet"))


@app.route("/send_message", methods=["POST"])
def send_message():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
    msg_text = request.form.get("message_text")
    if msg_text and msg_text.strip():
        new_msg = Message(
            teacher_id=session["user_id"],
            sender="teacher",
            message_text=msg_text.strip(),
        )
        db.session.add(new_msg)
        db.session.commit()
        flash("Сұрағыңыз админге жолданды!", "success")
    return redirect(url_for("teacher_cabinet"))


@app.route("/admin_reply/<int:msg_id>", methods=["POST"])
def admin_reply(msg_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    reply_text = request.form.get("reply_text")
    msg = Message.query.get_or_404(msg_id)
    if reply_text and reply_text.strip() and not msg.admin_reply:
        msg.admin_reply = reply_text.strip()
        db.session.commit()
        flash("Жауап сәтті жазылды!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/save_apparatus/<int:research_id>", methods=["POST"])
def save_apparatus(research_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
    research = Research.query.get_or_404(research_id)
    if research.teacher_id == session["user_id"]:
        research.relevance = request.form.get("relevance")
        research.goal = request.form.get("goal")
        research.tasks = request.form.get("tasks")
        research.hypothesis = request.form.get("hypothesis")
        research.expected_result = request.form.get("expected_result")
        db.session.commit()
        flash("Ғылыми аппарат сақталды.", "success")
    return redirect(url_for("teacher_cabinet"))


@app.route("/save_category_material/<int:research_id>", methods=["POST"])
def save_category_material(research_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))
    research = Research.query.get_or_404(research_id)
    if research.teacher_id == session["user_id"]:
        cat_type = request.form.get("cat_type")
        content = request.form.get("content")

        if cat_type == "lit":
            research.lit_review = content
        elif cat_type == "exp":
            research.experiment_analysis = content
        elif cat_type == "survey":
            research.survey_data = content
        elif cat_type == "refs":
            research.references_list = content

        db.session.commit()
        flash("Материал сақталды.", "success")
    return redirect(url_for("teacher_cabinet"))


@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST" and "approve_material" in request.form:
        res_id = request.form.get("research_id")
        mat_type = request.form.get("mat_type")
        feedback = request.form.get("mat_feedback", "Қабылданды")
        score = int(request.form.get("mat_score", 5))

        res_obj = Research.query.get(res_id)
        teacher_obj = User.query.get(res_obj.teacher_id)

        if mat_type == "apparatus":
            res_obj.apparatus_feedback = feedback
            res_obj.apparatus_score = score
            if not res_obj.apparatus_approved:
                res_obj.apparatus_approved = True
                teacher_obj.bonuses += score * 2
        elif mat_type == "lit":
            res_obj.lit_feedback = feedback
            res_obj.lit_score = score
            if not res_obj.lit_approved:
                res_obj.lit_approved = True
                teacher_obj.bonuses += score * 2
        elif mat_type == "exp":
            res_obj.exp_feedback = feedback
            res_obj.exp_score = score
            if not res_obj.exp_approved:
                res_obj.exp_approved = True
                teacher_obj.bonuses += score * 2
        elif mat_type == "survey":
            res_obj.survey_feedback = feedback
            res_obj.survey_score = score
            if not res_obj.survey_approved:
                res_obj.survey_approved = True
                teacher_obj.bonuses += score * 2
        elif mat_type == "refs":
            res_obj.refs_feedback = feedback
            res_obj.refs_score = score
            if not res_obj.refs_approved:
                res_obj.refs_approved = True
                teacher_obj.bonuses += score * 2

        db.session.commit()
        flash(f"Жұмыс бағаланды ({score}/10 балл) және ұпай есептелді!", "success")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST" and "doc_title" in request.form:
        doc_title = request.form.get("doc_title")
        if "doc_file" in request.files:
            file = request.files["doc_file"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                unique_name = f"doc_{int(datetime.now().timestamp())}_{filename}"
                file.save(
                    os.path.join(app.config["PDF_STORAGE_FOLDER"], unique_name)
                )

                new_doc = SharedDocument(
                    title=doc_title, filename=f"pdf_storage/{unique_name}"
                )
                db.session.add(new_doc)
                db.session.commit()
                flash("Әдістемелік файл сәтті жүктелді!", "success")
                return redirect(url_for("admin_dashboard"))

    teachers = User.query.filter_by(role="teacher").order_by(
        User.bonuses.desc()
    ).all()
    researches = Research.query.all()
    documents = SharedDocument.query.all()
    all_messages = Message.query.order_by(Message.created_at.desc()).all()

    return render_template_string(
        ADMIN_HTML,
        teachers=teachers,
        researches=researches,
        documents=documents,
        all_messages=all_messages,
        total_teachers=len(teachers),
    )


@app.route("/admin/delete/<int:research_id>")
def delete_research(research_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    research = Research.query.get_or_404(research_id)
    db.session.delete(research)
    db.session.commit()
    flash("Зерттеу жойылды.", "info")
    return redirect(url_for("admin_dashboard"))


# --- HTML ЖӘНЕ ДИЗАЙН БӨЛІМІ ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="kk">
<head>
    <meta charset="UTF-8">
    <title>Кіру - Ustaz Research Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fffde7; font-family: system-ui, -apple-system, sans-serif; font-size: 16px; font-weight: bold; }
        h2 { font-weight: 900; color: #0d47a1; font-size: 28px; }
        .card { border-radius: 16px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); background: #ffffff; border: 2px solid #ffe082; }
        .form-label { font-weight: bold; color: #0d47a1; }
        .btn-neon-blue { background: #00e5ff; color: #000; font-weight: bold; font-size: 18px; border-radius: 10px; padding: 10px; box-shadow: 0 0 12px #00e5ff; border: none; }
        .btn-neon-blue:hover { background: #00b8d4; box-shadow: 0 0 20px #00e5ff; }
    </style>
</head>
<body class="d-flex align-items-center justify-content-center vh-100">
    <div class="card p-5" style="width: 440px;">
        <h2 class="text-center mb-4">USTAZ RESEARCH PRO</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}{% for cat, msg in messages %}
                <div class="alert alert-{{ cat }} fw-bold">{{ msg }}</div>
            {% endfor %}{% endif %}
        {% endwith %}
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Логин:</label>
                <input type="text" name="username" id="usernameInput" class="form-control form-control-lg border-primary fw-bold" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Пароль:</label>
                <input type="password" name="password" id="passwordInput" class="form-control form-control-lg border-primary fw-bold" required>
            </div>
            <button type="submit" class="btn btn-neon-blue w-100 mb-3">КІРУ</button>
            <div class="d-flex justify-content-between">
                <a href="/register" class="fw-bold text-decoration-none">Тіркелу</a>
                <a href="#" onclick="fillAdmin()" class="fw-bold text-danger text-decoration-none">👑 Админ болып кіру</a>
            </div>
        </form>
    </div>
    <script>
        function fillAdmin() {
            document.getElementById('usernameInput').value = 'admin';
            document.getElementById('passwordInput').value = 'admin123';
        }
    </script>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="kk">
<head>
    <meta charset="UTF-8">
    <title>Тіркелу - Ustaz Research Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fffde7; font-family: system-ui, -apple-system, sans-serif; font-size: 16px; font-weight: bold; }
        h2 { font-weight: 900; color: #0d47a1; font-size: 28px; }
        .card { border-radius: 16px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); background: #ffffff; border: 2px solid #ffe082; }
        .form-label { font-weight: bold; color: #0d47a1; }
        .btn-neon-green { background: #00e676; color: #000; font-weight: bold; font-size: 18px; border-radius: 10px; padding: 10px; box-shadow: 0 0 12px #00e676; border: none; }
        .btn-neon-green:hover { background: #00c853; box-shadow: 0 0 20px #00e676; }
    </style>
</head>
<body class="d-flex align-items-center justify-content-center vh-100">
    <div class="card p-5" style="width: 480px;">
        <h2 class="text-center mb-4">Мұғалімді Тіркеу</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3">
                <label class="form-label">Аты-жөніңіз:</label>
                <input type="text" name="full_name" class="form-control form-control-lg border-primary fw-bold" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Санат:</label>
                <select name="category" class="form-select form-select-lg border-primary fw-bold">
                    {% for kat in data.kategoriya %}<option value="{{ kat }}">{{ kat }}</option>{% endfor %}
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Жеке суретіңіз (Аватар):</label>
                <input type="file" name="profile_pic" class="form-control form-control-lg border-primary fw-bold" accept="image/*">
            </div>
            <div class="mb-3">
                <label class="form-label">Логин:</label>
                <input type="text" name="username" class="form-control form-control-lg border-primary fw-bold" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Пароль:</label>
                <input type="password" name="password" class="form-control form-control-lg border-primary fw-bold" required>
            </div>
            <button type="submit" class="btn btn-neon-green w-100 mb-3">ТІРКЕЛУДІ АЯҚТАУ</button>
            <div class="text-center"><a href="/login" class="fw-bold text-decoration-none">← Кіруге оралу</a></div>
        </form>
    </div>
</body>
</html>
"""

TEACHER_HTML = """
<!DOCTYPE html>
<html lang="kk">
<head>
    <meta charset="UTF-8">
    <title>Мұғалім кабинеті - Ustaz Research Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fffde7; font-family: system-ui, -apple-system, sans-serif; font-size: 16px; font-weight: bold; }
        h2, h4, h5 { font-weight: 900; color: #0d47a1; }
        .card { border-radius: 16px; box-shadow: 0 8px 25px rgba(0,0,0,0.08); background: #ffffff; border: 2px solid #ffe082; }
        .form-label { font-weight: bold; color: #0d47a1; }
        .avatar-img { width: 80px; height: 80px; object-fit: cover; border-radius: 50%; border: 3px solid #ffab00; }
        .title-option-box { background: #fffde7; border: 2px solid #ffd54f; border-radius: 10px; padding: 15px; margin-bottom: 12px; font-weight: bold; }
        .quote-box { background: linear-gradient(135deg, #7c4dff, #00e5ff); color: white; border-radius: 16px; padding: 20px; font-weight: bold; box-shadow: 0 0 15px rgba(0,229,255,0.3); }
        .section-content { display: none; }
        .section-content.active { display: block; }
        .chat-box { max-height: 280px; overflow-y: auto; background: #fff; border: 2px solid #ffd54f; border-radius: 10px; padding: 12px; }

        .btn-neon-pink { background: #ff007f; color: #fff; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #ff007f; border: none; }
        .btn-neon-pink:hover { background: #e0006f; box-shadow: 0 0 18px #ff007f; color: #fff; }
        .btn-neon-purple { background: #9c27b0; color: #fff; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #9c27b0; border: none; }
        .btn-neon-cyan { background: #00bcd4; color: #000; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #00bcd4; border: none; }
        .btn-neon-yellow { background: #ffea00; color: #000; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #ffea00; border: none; }
        .btn-neon-orange { background: #ff6d00; color: #fff; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #ff6d00; border: none; }
        .btn-neon-green { background: #00e676; color: #000; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #00e676; border: none; }
        
        /* ШАРШЫ ИКОНКАЛАР ЖӘНЕ АСТЫНДАҒЫ АТАУЫ */
        .square-action-container {
            display: flex;
            gap: 15px;
        }
        .square-action-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .square-icon-btn {
            width: 55px;
            height: 55px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            transition: 0.2s;
            border: 2px solid #fff;
            text-decoration: none;
            cursor: pointer;
        }
        .square-icon-btn:hover {
            transform: scale(1.08);
        }
        .square-btn-label {
            font-size: 13px;
            font-weight: 800;
            color: #0d47a1;
            margin-top: 5px;
            text-align: center;
            max-width: 80px;
        }
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="card p-4 mb-4 shadow-sm">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
                <div class="d-flex align-items-center gap-3">
                    <img src="{{ url_for('static', filename='uploads/' + teacher.profile_pic) if teacher.profile_pic != 'default_avatar.png' else 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png' }}" class="avatar-img" alt="Сурет">
                    <div>
                        <div class="d-flex align-items-center gap-3">
                            <h2 class="mb-0 fw-bold">{{ teacher.full_name }}</h2>
                            <span class="fs-4 fw-bold" style="color: #d50000;">⭐ #{{ teacher_rank }}-орын</span>
                        </div>
                        <p class="text-muted mb-0 fw-bold">{{ teacher.category }} | <span class="text-success">⭐ Бонус: <b>{{ teacher.bonuses }} ұпай</b></span></p>
                    </div>
                </div>

                <!-- ОҢ ЖАҚТЫҢ АШЫҚ АЛАҢЫНДАҒЫ ШАРШЫ БАТЫРМАЛАР (Әдістемелік қойма мен ЖІ) -->
                <div class="square-action-container">
                    <div class="square-action-item">
                        <button type="button" class="square-icon-btn btn-neon-green text-dark" onclick="openSection('storage', document.getElementById('dummyStorageTab'))" title="Әдістемелік қойма">
                            📚
                        </button>
                        <span class="square-btn-label">Қойма</span>
                    </div>
                    <div class="square-action-item">
                        <button type="button" class="square-icon-btn btn-neon-yellow text-dark" title="Жасанды Интеллект" data-bs-toggle="modal" data-bs-target="#aiModal">
                            🤖
                        </button>
                        <span class="square-btn-label">ЖІ (AI)</span>
                    </div>
                    <div class="square-action-item">
                        <a href="/logout" class="square-icon-btn btn-neon-pink text-white text-decoration-none" title="Шығу">
                            🚪
                        </a>
                        <span class="square-btn-label">Шығу</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="quote-box mb-4 shadow">
            <h4 class="text-white fw-bold">💡 Күннің әдістемелік кеңесі:</h4>
            <p class="mb-1 fst-italic">«Зерттеу жұмысы — мұғалім шеберлігінің шыңы.»</p>
            <small class="text-light">🏆 <b>Рейтинг марапаттары:</b> 1, 2, 3-орын алған зерттеушілерге Республикалық Сертификаттар беріледі!</small>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}{% for cat, msg in messages %}
                <div class="alert alert-success fw-bold">{{ msg }}</div>
            {% endfor %}{% endif %}
        {% endwith %}

        <!-- МҰҒАЛІМ КАБИНЕТІНДЕГІ НЕГІЗГІ БАТЫРМАЛАР -->
        <div class="d-flex flex-wrap gap-3 mb-4">
            <button class="btn btn-neon-pink tab-btn active" onclick="openSection('constructor', this)" id="dummyStorageTab">🛠️ Зерттеу Конструкторы</button>
            <button class="btn btn-neon-purple tab-btn" onclick="openSection('calendar', this)">📅 Зерттеу Күнтізбесі</button>
            <button class="btn btn-neon-cyan tab-btn" onclick="openSection('researches', this)">📁 Менің зерттеулерім</button>
            <button class="btn btn-neon-yellow tab-btn text-dark" onclick="openSection('chat', this)">💬 Админмен сөйлесу</button>
            <button class="btn btn-neon-orange tab-btn" onclick="openSection('bonuses', this)">⭐ Сертификаттар</button>
        </div>

        <!-- 1. ЗЕРТТЕУ КОНСТРУКТОРЫ -->
        <div id="constructor" class="card p-4 mb-4 section-content active shadow-sm">
            <h4 class="text-primary fw-bold mb-4">Зерттеу Конструкторы</h4>
            <form method="POST">
                <input type="hidden" name="action_type" value="save_research">
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label class="form-label">Пән:</label>
                        <select name="subject" id="subjectSelect" class="form-select border-primary fw-bold" required onchange="updateProblems()">
                            <option value="">Пәнді таңдаңыз...</option>
                            {% for pan in data.pander %}<option value="{{ pan }}">{{ pan }}</option>{% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Сынып:</label>
                        <select name="grade" id="gradeSelect" class="form-select border-primary fw-bold" required onchange="generateTitles()">
                            {% for s in data.synyp %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Дағды:</label>
                        <select name="skill" id="skillSelect" class="form-select border-primary fw-bold" required onchange="generateTitles()">
                            {% for d in data.dagdy %}<option value="{{ d }}">{{ d }}</option>{% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Әдіс:</label>
                        <select name="method" id="methodSelect" class="form-select border-primary fw-bold" required onchange="generateTitles()">
                            {% for a in data.adister %}<option value="{{ a }}">{{ a }}</option>{% endfor %}
                        </select>
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label">Зерттеу проблемасы:</label>
                    <select name="problem" id="problemSelect" class="form-select border-primary fw-bold" required onchange="generateTitles()">
                        <option value="">Алдымен пәнді таңдаңыз...</option>
                    </select>
                </div>

                <div id="titlesSection" style="display: none;" class="mb-4 p-3 border border-primary rounded bg-light">
                    <h5 class="fw-bold text-primary mb-3">📌 Тақырып нұсқалары (Біреуін таңдаңыз):</h5>
                    <div id="titlesContainer"></div>
                </div>

                <button type="submit" id="submitBtn" class="btn btn-neon-green w-100 py-3 text-dark fw-bold" style="display: none;">ЗЕРТТЕУДІ ЖЕКЕ КАБИНЕТТЕ САҚТАУ</button>
            </form>
        </div>

        <!-- 2. ЗЕРТТЕУ КҮНТІЗБЕСІ -->
        <div id="calendar" class="card p-4 mb-4 section-content shadow-sm">
            <h4 class="text-primary fw-bold mb-3">📅 Зерттеу жұмысының күнтізбесі (Планнер)</h4>
            <form method="POST" class="row g-3 mb-3">
                <input type="hidden" name="action_type" value="add_task">
                <div class="col-md-6"><input type="text" name="task_name" class="form-control fw-bold" placeholder="Тапсырма атауы..." required></div>
                <div class="col-md-4"><input type="date" name="task_date" class="form-control fw-bold" required></div>
                <div class="col-md-2"><button type="submit" class="btn btn-neon-cyan w-100 text-dark fw-bold">ҚОСУ</button></div>
            </form>

            <ul class="list-group">
                {% for task in my_tasks %}
                    <li class="list-group-item d-flex justify-content-between align-items-center py-2 fw-bold">
                        <div>
                            <span class="badge bg-secondary me-3">{{ task.task_date }}</span>
                            <span class="{{ 'text-decoration-line-through text-muted' if task.is_completed else 'text-dark' }}">{{ task.task_name }}</span>
                        </div>
                        <a href="/toggle_task/{{ task.id }}" class="btn {{ 'btn-success' if task.is_completed else 'btn-outline-secondary' }} btn-sm fw-bold">
                            {{ 'Орындалды ✓' if task.is_completed else 'Белгі қою' }}
                        </a>
                    </li>
                {% else %}
                    <p class="text-muted">Әзірге жоспарланған тапсырмалар жоқ.</p>
                {% endfor %}
            </ul>
        </div>

        <!-- 3. МЕНІҢ ЗЕРТТЕУЛЕРІМ -->
        <div id="researches" class="card p-4 mb-4 section-content shadow-sm">
            <h4 class="text-primary fw-bold mb-3">📁 Менің жеке кабинетімдегі сақталған зерттеулерім</h4>
            {% for r in researches %}
            <div class="card border-primary mb-4 p-3 bg-light shadow-sm">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="fw-bold text-dark">#{{ r.id }} - {{ r.subject }} ({{ r.grade }})</h5>
                    <span class="badge bg-secondary">{{ r.status }}</span>
                </div>
                <p class="mb-2 fw-bold"><b>Таңдалған тақырып:</b> {{ r.selected_title }}</p>
                
                <div class="d-flex flex-wrap gap-2 mb-3">
                    <button class="btn btn-neon-cyan text-dark fw-bold btn-sm" type="button" data-bs-toggle="collapse" data-bs-target="#apparatus{{ r.id }}">
                        🔬 Ғылыми аппарат {% if r.apparatus_approved %}(Баға: {{ r.apparatus_score }}/10 ✓){% endif %}
                    </button>
                    <button class="btn btn-neon-green text-dark fw-bold btn-sm" type="button" data-bs-toggle="collapse" data-bs-target="#categories{{ r.id }}">
                        🗂️ Зерттеу материалдары (Қалташалар)
                    </button>
                </div>

                <div class="collapse mt-2" id="apparatus{{ r.id }}">
                    <div class="card card-body border-info bg-white p-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="fw-bold text-info mb-0">🔬 Ғылыми аппарат және бағалау:</h6>
                            <button class="btn btn-outline-secondary btn-sm fw-bold" type="button" data-bs-toggle="modal" data-bs-target="#critApparatus">📊 Критерійлер</button>
                        </div>
                        <div class="alert alert-info py-1 mb-2 small"><b>Админ бағасы:</b> {{ r.apparatus_score }}/10 | <b>Пікір:</b> {{ r.apparatus_feedback }}</div>
                        <form method="POST" action="/save_apparatus/{{ r.id }}">
                            <div class="mb-2"><label class="form-label small">Өзектілігі:</label><textarea name="relevance" class="form-control form-control-sm fw-bold" rows="2">{{ r.relevance }}</textarea></div>
                            <div class="mb-2"><label class="form-label small">Мақсаты:</label><input type="text" name="goal" class="form-control form-control-sm fw-bold" value="{{ r.goal }}"></div>
                            <div class="mb-2"><label class="form-label small">Міндеттері:</label><textarea name="tasks" class="form-control form-control-sm fw-bold" rows="2">{{ r.tasks }}</textarea></div>
                            <div class="mb-2"><label class="form-label small">Болжамы:</label><input type="text" name="hypothesis" class="form-control form-control-sm fw-bold" value="{{ r.hypothesis }}"></div>
                            <div class="mb-2"><label class="form-label small">Күтілетін нәтижелер:</label><textarea name="expected_result" class="form-control form-control-sm fw-bold" rows="2">{{ r.expected_result }}</textarea></div>
                            <button type="submit" class="btn btn-neon-cyan text-dark btn-sm fw-bold w-100">САҚТАУ</button>
                        </form>
                    </div>
                </div>

                <div class="collapse mt-2" id="categories{{ r.id }}">
                    <div class="card card-body border-success bg-white p-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="fw-bold text-success mb-0">🗂️ Материалдар категориялары:</h6>
                            <button class="btn btn-outline-secondary btn-sm fw-bold" type="button" data-bs-toggle="modal" data-bs-target="#critMaterials">📊 Критерійлер</button>
                        </div>
                        
                        <ul class="nav nav-tabs small fw-bold" id="matTab{{ r.id }}" role="tablist">
                            <li class="nav-item"><button class="nav-link active text-success" data-bs-toggle="tab" data-bs-target="#lit{{ r.id }}" type="button">📖 Әдебиет</button></li>
                            <li class="nav-item"><button class="nav-link text-success" data-bs-toggle="tab" data-bs-target="#exp{{ r.id }}" type="button">📊 Эксперимент</button></li>
                            <li class="nav-item"><button class="nav-link text-success" data-bs-toggle="tab" data-bs-target="#survey{{ r.id }}" type="button">📝 Сауалнама</button></li>
                            <li class="nav-item"><button class="nav-link text-success" data-bs-toggle="tab" data-bs-target="#refs{{ r.id }}" type="button">📚 Әдебиеттер</button></li>
                        </ul>

                        <div class="tab-content pt-3" id="matTabContent{{ r.id }}">
                            <div class="tab-pane fade show active" id="lit{{ r.id }}">
                                <div class="alert alert-light border py-1 mb-2 small fw-bold"><b>Баға:</b> {{ r.lit_score }}/10 | <b>Пікір:</b> {{ r.lit_feedback }}</div>
                                <form method="POST" action="/save_category_material/{{ r.id }}">
                                    <input type="hidden" name="cat_type" value="lit">
                                    <textarea name="content" class="form-control form-control-sm fw-bold mb-2" rows="3" placeholder="Әдебиеттік шолу...">{{ r.lit_review }}</textarea>
                                    <button type="submit" class="btn btn-neon-green text-dark btn-sm fw-bold w-100">САҚТАУ</button>
                                </form>
                            </div>
                            <div class="tab-pane fade" id="exp{{ r.id }}">
                                <div class="alert alert-light border py-1 mb-2 small fw-bold"><b>Баға:</b> {{ r.exp_score }}/10 | <b>Пікір:</b> {{ r.exp_feedback }}</div>
                                <form method="POST" action="/save_category_material/{{ r.id }}">
                                    <input type="hidden" name="cat_type" value="exp">
                                    <textarea name="content" class="form-control form-control-sm fw-bold mb-2" rows="3" placeholder="Эксперимент талдауы...">{{ r.experiment_analysis }}</textarea>
                                    <button type="submit" class="btn btn-neon-green text-dark btn-sm fw-bold w-100">САҚТАУ</button>
                                </form>
                            </div>
                            <div class="tab-pane fade" id="survey{{ r.id }}">
                                <div class="alert alert-light border py-1 mb-2 small fw-bold"><b>Баға:</b> {{ r.survey_score }}/10 | <b>Пікір:</b> {{ r.survey_feedback }}</div>
                                <form method="POST" action="/save_category_material/{{ r.id }}">
                                    <input type="hidden" name="cat_type" value="survey">
                                    <textarea name="content" class="form-control form-control-sm fw-bold mb-2" rows="3" placeholder="Сауалнама нәтижелері...">{{ r.survey_data }}</textarea>
                                    <button type="submit" class="btn btn-neon-green text-dark btn-sm fw-bold w-100">САҚТАУ</button>
                                </form>
                            </div>
                            <div class="tab-pane fade" id="refs{{ r.id }}">
                                <div class="alert alert-light border py-1 mb-2 small fw-bold"><b>Баға:</b> {{ r.refs_score }}/10 | <b>Пікір:</b> {{ r.refs_feedback }}</div>
                                <form method="POST" action="/save_category_material/{{ r.id }}">
                                    <input type="hidden" name="cat_type" value="refs">
                                    <textarea name="content" class="form-control form-control-sm fw-bold mb-2" rows="3" placeholder="Әдебиеттер тізімі...">{{ r.references_list }}</textarea>
                                    <button type="submit" class="btn btn-neon-green text-dark btn-sm fw-bold w-100">САҚТАУ</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
            {% else %}
            <p class="text-muted">Әзірге сақталған зерттеулеріңіз жоқ.</p>
            {% endfor %}
        </div>

        <!-- 4. ӘДІСТЕМЕЛІК ҚОЙМА (ОҢ ЖАҚ ШАРШЫ БАТЫРМАСЫ АРҚЫЛЫ АШЫЛАДЫ) -->
        <div id="storage" class="card p-4 mb-4 section-content shadow-sm">
            <h4 class="text-success fw-bold mb-3">📚 Әдістемелік ақпараттық қойма (Админ материалдары)</h4>
            {% if shared_docs %}
                <ul class="list-group">
                {% for doc in shared_docs %}
                    <li class="list-group-item d-flex justify-content-between align-items-center py-2 fw-bold">
                        <span>📄 {{ doc.title }}</span>
                        <a href="{{ url_for('static', filename=doc.filename) }}" target="_blank" class="btn btn-neon-green text-dark btn-sm">ҚАРАУ / ЖҮКТЕУ</a>
                    </li>
                {% endfor %}
                </ul>
            {% else %}
                <p class="text-muted">Әзірге ақпараттық қоймада материалдар жоқ.</p>
            {% endif %}
        </div>

        <!-- 5. АДМИНМЕН СӨЙЛЕСУ (ЧАТ) -->
        <div id="chat" class="card p-4 mb-4 section-content shadow-sm">
            <h4 class="text-warning fw-bold mb-3">💬 Админге қойылатын сұрақтар мен хабарламалар</h4>
            <div class="chat-box mb-3">
                {% for msg in teacher_messages %}
                    <div class="mb-2 p-2 rounded bg-light border fw-bold">
                        <small class="d-block text-primary">Сұрағыңыз: {{ msg.message_text }}</small>
                        {% if msg.admin_reply %}
                            <div class="alert alert-success mt-1 mb-0 py-1">👑 <b>Админ жауабы:</b> {{ msg.admin_reply }}</div>
                        {% else %}
                            <span class="text-muted fw-normal small">Админ әлі жауап берген жоқ...</span>
                        {% endif %}
                    </div>
                {% else %}
                    <p class="text-muted text-center my-3">Әзірге сұрақтарыңыз жоқ.</p>
                {% endfor %}
            </div>
            <form method="POST" action="/send_message">
                <div class="input-group">
                    <input type="text" name="message_text" class="form-control border-primary fw-bold" placeholder="Админге сұрақ жазу..." required>
                    <button type="submit" class="btn btn-neon-yellow text-dark fw-bold px-4">ЖІБЕРУ</button>
                </div>
            </form>
        </div>

        <!-- 6. БОНУС ЖӘНЕ СЕРТИФИКАТТАР -->
        <div id="bonuses" class="card p-4 mb-4 section-content shadow-sm text-center">
            <h4 class="text-warning fw-bold mb-3">⭐ Бонус жүйесі және Сертификаттар</h4>
            <div class="display-4 fw-bold text-success mb-2">{{ teacher.bonuses }} ұпай</div>
            <p class="text-muted mb-3">Жинаған ұпайларыңызға сай <b>Марапат атаулары мен Сертификаттар</b>:</p>
            
            <div class="row g-3 text-start fw-bold">
                <div class="col-md-4">
                    <div class="p-3 border rounded bg-light shadow-sm">
                        <h5 class="fw-bold text-primary">🥉 1-ші деңгей (50+ ұпай)</h5>
                        <p class="mb-1"><b>Атауы:</b> «Ізденуші-зерттеуші»</p>
                        <p class="text-success mb-0">Статус: {{ 'Берілді ✓' if teacher.bonuses >= 50 else 'Жиналуда...' }}</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="p-3 border rounded bg-light shadow-sm">
                        <h5 class="fw-bold text-success">🥈 2-ші деңгей (100+ ұпай)</h5>
                        <p class="mb-1"><b>Атауы:</b> «Ғылыми әдіскер»</p>
                        <p class="text-success mb-0">Статус: {{ 'Берілді ✓' if teacher.bonuses >= 100 else 'Жиналуда...' }}</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="p-3 border rounded bg-light shadow-sm">
                        <h5 class="fw-bold text-danger">🥇 3-ші деңгей (150+ ұпай)</h5>
                        <p class="mb-1"><b>Атауы:</b> «Академиялық көшбасшы»</p>
                        <p class="text-success mb-0">Статус: {{ 'Берілді ✓' if teacher.bonuses >= 150 else 'Жиналуда...' }}</p>
                    </div>
                </div>
            </div>

            {% if teacher_rank <= 3 %}
                <div class="alert alert-success mt-3 fw-bold">
                    🎉 Құттықтаймыз! Сіз жалпы рейтингте ТОП-3 қатарындасыз (#{{ teacher_rank }}-орын). Сізге Республикалық Сертификат беріледі!
                </div>
            {% endif %}
        </div>
    </div>

    <!-- МОДАЛДЫ ТЕРЕЗЕЛЕР -->
    <div class="modal fade" id="aiModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content p-4 fw-bold">
          <div class="modal-header bg-warning text-dark"><h5 class="modal-title fw-bold">🤖 Зерттеуде қолданылатын ЖІ (AI) сілтемелері</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <p>Зерттеу жұмысыңызды сапалы жүргізу үшін мына жасанды интеллект құралдарын пайдалана аласыз:</p>
            <ul class="list-group mb-3">
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>💬 <b>ChatGPT</b> (Тақырып құру және мәтін өңдеу)</span>
                <a href="https://chatgpt.com" target="_blank" class="btn btn-sm btn-dark">Өту</a>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>🧠 <b>Claude AI</b> (Ғылыми мақалалар мен талдау жасау)</span>
                <a href="https://claude.ai" target="_blank" class="btn btn-sm btn-dark">Өту</a>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>✨ <b>Google Gemini</b> (Идеялар мен жоспар құру)</span>
                <a href="https://gemini.google.com" target="_blank" class="btn btn-sm btn-dark">Өту</a>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>🔍 <b>Consensus</b> (Ғылыми дереккөздерді іздеуші AI)</span>
                <a href="https://consensus.app" target="_blank" class="btn btn-sm btn-dark">Өту</a>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>📚 <b>Elicit</b> (Әдебиеттік шолу жасауға арналған AI)</span>
                <a href="https://elicit.com" target="_blank" class="btn btn-sm btn-dark">Өту</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="critApparatus" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content p-3 fw-bold">
          <div class="modal-header bg-info text-white"><h5 class="modal-title">🔬 Ғылыми аппарат критерийлері (1-10 балл)</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body small">
            <ul>
              <li><b>Өзектілігі (1-2 балл):</b> Мәселенің маңыздылығы.</li>
              <li><b>Мақсаты мен міндеттері (1-2 балл):</b> Логикалық жүйелілігі.</li>
              <li><b>Болжамы (1-2 балл):</b> Ғылыми негізделгені.</li>
              <li><b>Әдістер мен нәтижелер (1-4 балл):</b> Дұрыс таңдалғаны.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="critMaterials" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content p-3 fw-bold">
          <div class="modal-header bg-success text-white"><h5 class="modal-title">🗂️ Материалдар критерийлері (1-10 балл)</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body small">
            <ul>
              <li><b>Әдебиеттік шолу (1-10):</b> Еңбектердің талдануы.</li>
              <li><b>Эксперимент (1-10):</b> Практикалық мысалдар.</li>
              <li><b>Сауалнама (1-10):</b> Нәтижелердің қамтылуы.</li>
              <li><b>Әдебиеттер (1-10):</b> Академиялық ресімделуі.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function openSection(sectionId, btnElement) {
            document.querySelectorAll('.section-content').forEach(sec => sec.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(btn => { btn.classList.remove('active'); });
            document.getElementById(sectionId).classList.add('active');
            btnElement.classList.add('active');
        }

        const problemsData = {{ data.problemalar | tojson }};
        function updateProblems() {
            const subject = document.getElementById('subjectSelect').value;
            const problemSelect = document.getElementById('problemSelect');
            problemSelect.innerHTML = '<option value="">Проблеманы таңдаңыз...</option>';
            if (subject && problemsData[subject]) {
                problemsData[subject].forEach(prob => {
                    const opt = document.createElement('option');
                    opt.value = prob;
                    opt.textContent = prob;
                    problemSelect.appendChild(opt);
                });
            }
            generateTitles();
        }

        function generateTitles() {
            const subject = document.getElementById('subjectSelect').value;
            const grade = document.getElementById('gradeSelect').value;
            const skill = document.getElementById('skillSelect').value;
            const method = document.getElementById('methodSelect').value;
            const problem = document.getElementById('problemSelect').value;

            const titlesSection = document.getElementById('titlesSection');
            const titlesContainer = document.getElementById('titlesContainer');
            const submitBtn = document.getElementById('submitBtn');

            if (!subject || !problem) {
                titlesSection.style.display = 'none';
                submitBtn.style.display = 'none';
                return;
            }

            const t1 = `${subject} сабағында ${grade} оқушыларының ${skill.toLowerCase()} дағдыларын дамыту арқылы ${problem} мәселесін шешуде ${method.toLowerCase()} тәсілін қолдану`;
            const t2 = `${grade} оқушыларының ${subject.toLowerCase()} пәнінде ${problem} бағытындағы қиындықтарын жою мақсатында ${method.toLowerCase()} әдістемесін енгізу ерекшеліктері`;
            const t3 = `Педагог ретінде ${subject} курсында ${skill.toLowerCase()} қалыптастыру және ${problem} мәселесін ${method.toLowerCase()} арқылы зерттеу`;

            titlesContainer.innerHTML = `
                <div class="title-option-box">
                    <input class="form-check-input me-3" type="radio" name="selected_title" id="t1" value="${t1}" style="width: 22px; height: 22px;" required checked>
                    <label class="form-check-label fw-bold text-dark" for="t1">${t1}</label>
                </div>
                <div class="title-option-box">
                    <input class="form-check-input me-3" type="radio" name="selected_title" id="t2" value="${t2}" style="width: 22px; height: 22px;">
                    <label class="form-check-label fw-bold text-dark" for="t2">${t2}</label>
                </div>
                <div class="title-option-box">
                    <input class="form-check-input me-3" type="radio" name="selected_title" id="t3" value="${t3}" style="width: 22px; height: 22px;">
                    <label class="form-check-label fw-bold text-dark" for="t3">${t3}</label>
                </div>
            `;
            titlesSection.style.display = 'block';
            submitBtn.style.display = 'block';
        }
    </script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="kk">
<head>
    <meta charset="UTF-8">
    <title>Админ панелі - Ustaz Research Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #fffde7; font-family: system-ui, -apple-system, sans-serif; font-size: 16px; font-weight: bold; }
        h2, h4 { font-weight: 900; color: #0d47a1; }
        .card { border-radius: 16px; box-shadow: 0 8px 25px rgba(0,0,0,0.08); background: #ffffff; border: 2px solid #ffe082; }
        .admin-section { display: none; }
        .admin-section.active { display: block; }
        .btn-neon-pink { background: #ff007f; color: #fff; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #ff007f; border: none; }
        .btn-neon-pink:hover { background: #e0006f; box-shadow: 0 0 18px #ff007f; color: #fff; }
        .btn-neon-cyan { background: #00bcd4; color: #000; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #00bcd4; border: none; }
        .btn-neon-green { background: #00e676; color: #000; font-weight: bold; border-radius: 10px; padding: 10px 20px; box-shadow: 0 0 10px #00e676; border: none; }
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
            <h2>👑 ADMIN: Басқару Панелі</h2>
            <a href="/logout" class="btn btn-danger btn-neon-pink">🚪 ШЫҒУ</a>
        </div>

        <!-- АДМИН ПАНЕЛІНДЕГІ ЖЕКЕ ТАБТАР (НЕГІЗГІ БЕТТЕ ТЕК РЕЙТИНГ) -->
        <div class="d-flex flex-wrap gap-3 mb-4">
            <button class="btn btn-neon-green admin-tab-btn active text-dark" onclick="openAdminTab('tab-rating', this)">🏆 Мұғалімдер рейтингі (Негізгі бет)</button>
            <button class="btn btn-neon-cyan admin-tab-btn text-dark" onclick="openAdminTab('tab-storage', this)">📤 Әдістемелік қоймаға PDF жүктеу</button>
            <button class="btn btn-neon-pink admin-tab-btn" onclick="openAdminTab('tab-grading', this)">🔬 Жұмыстарды бағалау (1-10 балл)</button>
            <button class="btn btn-warning admin-tab-btn text-dark fw-bold" onclick="openAdminTab('tab-chat', this)">💬 Мұғалімдердің сұрақтары</button>
        </div>

        <!-- 1. НЕГІЗГІ БЕТ: РЕЙТИНГ -->
        <div id="tab-rating" class="card p-4 mb-4 admin-section active shadow-sm">
            <h4 class="text-success fw-bold mb-3">🏆 Зерттеуші мұғалімдердің рейтингі (Негізгі бет)</h4>
            <table class="table table-hover align-middle fw-bold">
                <thead class="table-success">
                    <tr><th>Орын</th><th>Мұғалім</th><th>Санат</th><th>Бонус</th><th>Сертификат мәртебесі</th></tr>
                </thead>
                <tbody>
                    {% for t in teachers %}
                    <tr>
                        <td class="fw-bold">#{{ loop.index }}</td>
                        <td class="fw-semibold">{{ t.full_name }}</td>
                        <td>{{ t.category }}</td>
                        <td><span class="badge bg-warning text-dark">{{ t.bonuses }} ⭐ ұпай</span></td>
                        <td>
                            {% if loop.index == 1 %}<span class="badge bg-danger">🥇 1-орын (Сертификат)</span>
                            {% elif loop.index == 2 %}<span class="badge bg-primary">🥈 2-орын (Сертификат)</span>
                            {% elif loop.index == 3 %}<span class="badge bg-success">🥉 3-орын (Сертификат)</span>
                            {% else %}<span class="text-muted">Қатысушы</span>{% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- 2. ӘДІСТЕМЕЛІК ҚОЙМАҒА PDF ЖҮКТЕУ -->
        <div id="tab-storage" class="card p-4 mb-4 admin-section shadow-sm">
            <h4 class="text-primary fw-bold mb-3">📤 Әдістемелік қоймаға PDF материал жүктеу</h4>
            <form method="POST" enctype="multipart/form-data" class="row g-3">
                <div class="col-md-5"><input type="text" name="doc_title" class="form-control fw-bold" placeholder="Құжат атауы" required></div>
                <div class="col-md-5"><input type="file" name="doc_file" class="form-control fw-bold" accept=".pdf" required></div>
                <div class="col-md-2"><button type="submit" class="btn btn-neon-cyan w-100">ЖҮКТЕУ</button></div>
            </form>
        </div>

        <!-- 3. ЗЕРТТЕУЛЕРДІ БАҒАЛАУ (1-10 БАЛЛ) -->
        <div id="tab-grading" class="card p-4 mb-4 admin-section shadow-sm">
            <h4 class="text-primary fw-bold mb-3">🔬 Зерттеушілердің жұмыстарын бөлек бөлімдер бойынша бағалау (1-10 балл)</h4>
            {% for r in researches %}
            <div class="card border-primary mb-4 p-3 bg-light">
                <h5 class="fw-bold text-dark">Мұғалім: {{ r.teacher.full_name }} | Тақырып: {{ r.selected_title }}</h5>
                
                <div class="d-flex flex-wrap gap-2 mt-3">
                    <button class="btn btn-neon-cyan text-dark btn-sm fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#admApp{{ r.id }}">🔬 Ғылыми аппарат</button>
                    <button class="btn btn-neon-green text-dark btn-sm fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#admLit{{ r.id }}">📖 Әдебиеттік шолу</button>
                    <button class="btn btn-neon-green text-dark btn-sm fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#admExp{{ r.id }}">📊 Эксперимент</button>
                    <button class="btn btn-neon-green text-dark btn-sm fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#admSurvey{{ r.id }}">📝 Сауалнама</button>
                    <button class="btn btn-neon-green text-dark btn-sm fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#admRefs{{ r.id }}">📚 Әдебиеттер</button>
                </div>

                <div class="collapse mt-3" id="admApp{{ r.id }}">
                    <div class="card card-body bg-white border-info fw-bold">
                        <h6 class="text-info fw-bold">🔬 Ғылыми аппарат (Бағасы: {{ r.apparatus_score }}/10)</h6>
                        <p class="small mb-1"><b>Өзектілігі:</b> {{ r.relevance }}</p>
                        <p class="small mb-1"><b>Мақсаты:</b> {{ r.goal }}</p>
                        <p class="small mb-1"><b>Міндеттері:</b> {{ r.tasks }}</p>
                        <p class="small mb-1"><b>Болжамы:</b> {{ r.hypothesis }}</p>
                        <p class="small mb-3"><b>Күтілетін нәтиже:</b> {{ r.expected_result }}</p>
                        <form method="POST" class="row g-2 align-items-center">
                            <input type="hidden" name="research_id" value="{{ r.id }}">
                            <input type="hidden" name="mat_type" value="apparatus">
                            <div class="col-md-3"><input type="number" name="mat_score" min="1" max="10" class="form-control form-control-sm fw-bold" value="{{ r.apparatus_score or 5 }}" required></div>
                            <div class="col-md-6"><input type="text" name="mat_feedback" class="form-control form-control-sm fw-bold" value="{{ r.apparatus_feedback }}" required></div>
                            <div class="col-md-3"><button type="submit" name="approve_material" value="1" class="btn btn-success btn-sm w-100 fw-bold">БАҒАЛАУ</button></div>
                        </form>
                    </div>
                </div>

                <div class="collapse mt-3" id="admLit{{ r.id }}">
                    <div class="card card-body bg-white border-success fw-bold">
                        <h6 class="text-success fw-bold">📖 Әдебиеттік шолу (Бағасы: {{ r.lit_score }}/10)</h6>
                        <div class="p-2 border bg-light small mb-2">{{ r.lit_review or 'Материал енгізілмеген' }}</div>
                        <form method="POST" class="row g-2 align-items-center">
                            <input type="hidden" name="research_id" value="{{ r.id }}">
                            <input type="hidden" name="mat_type" value="lit">
                            <div class="col-md-3"><input type="number" name="mat_score" min="1" max="10" class="form-control form-control-sm fw-bold" value="{{ r.lit_score or 5 }}" required></div>
                            <div class="col-md-6"><input type="text" name="mat_feedback" class="form-control form-control-sm fw-bold" value="{{ r.lit_feedback }}" required></div>
                            <div class="col-md-3"><button type="submit" name="approve_material" value="1" class="btn btn-success btn-sm w-100 fw-bold">БАҒАЛАУ</button></div>
                        </form>
                    </div>
                </div>

                <div class="collapse mt-3" id="admExp{{ r.id }}">
                    <div class="card card-body bg-white border-success fw-bold">
                        <h6 class="text-success fw-bold">📊 Эксперимент (Бағасы: {{ r.exp_score }}/10)</h6>
                        <div class="p-2 border bg-light small mb-2">{{ r.experiment_analysis or 'Материал енгізілмеген' }}</div>
                        <form method="POST" class="row g-2 align-items-center">
                            <input type="hidden" name="research_id" value="{{ r.id }}">
                            <input type="hidden" name="mat_type" value="exp">
                            <div class="col-md-3"><input type="number" name="mat_score" min="1" max="10" class="form-control form-control-sm fw-bold" value="{{ r.exp_score or 5 }}" required></div>
                            <div class="col-md-6"><input type="text" name="mat_feedback" class="form-control form-control-sm fw-bold" value="{{ r.exp_feedback }}" required></div>
                            <div class="col-md-3"><button type="submit" name="approve_material" value="1" class="btn btn-success btn-sm w-100 fw-bold">БАҒАЛАУ</button></div>
                        </form>
                    </div>
                </div>

                <div class="collapse mt-3" id="admSurvey{{ r.id }}">
                    <div class="card card-body bg-white border-success fw-bold">
                        <h6 class="text-success fw-bold">📝 Сауалнама (Бағасы: {{ r.survey_score }}/10)</h6>
                        <div class="p-2 border bg-light small mb-2">{{ r.survey_data or 'Материал енгізілмеген' }}</div>
                        <form method="POST" class="row g-2 align-items-center">
                            <input type="hidden" name="research_id" value="{{ r.id }}">
                            <input type="hidden" name="mat_type" value="survey">
                            <div class="col-md-3"><input type="number" name="mat_score" min="1" max="10" class="form-control form-control-sm fw-bold" value="{{ r.survey_score or 5 }}" required></div>
                            <div class="col-md-6"><input type="text" name="mat_feedback" class="form-control form-control-sm fw-bold" value="{{ r.survey_feedback }}" required></div>
                            <div class="col-md-3"><button type="submit" name="approve_material" value="1" class="btn btn-success btn-sm w-100 fw-bold">БАҒАЛАУ</button></div>
                        </form>
                    </div>
                </div>

                <div class="collapse mt-3" id="admRefs{{ r.id }}">
                    <div class="card card-body bg-white border-success fw-bold">
                        <h6 class="text-success fw-bold">📚 Әдебиеттер (Бағасы: {{ r.refs_score }}/10)</h6>
                        <div class="p-2 border bg-light small mb-2">{{ r.references_list or 'Материал енгізілмеген' }}</div>
                        <form method="POST" class="row g-2 align-items-center">
                            <input type="hidden" name="research_id" value="{{ r.id }}">
                            <input type="hidden" name="mat_type" value="refs">
                            <div class="col-md-3"><input type="number" name="mat_score" min="1" max="10" class="form-control form-control-sm fw-bold" value="{{ r.refs_score or 5 }}" required></div>
                            <div class="col-md-6"><input type="text" name="mat_feedback" class="form-control form-control-sm fw-bold" value="{{ r.refs_feedback }}" required></div>
                            <div class="col-md-3"><button type="submit" name="approve_material" value="1" class="btn btn-success btn-sm w-100 fw-bold">БАҒАЛАУ</button></div>
                        </form>
                    </div>
                </div>

            </div>
            {% endfor %}
        </div>

        <!-- 4. МҰҒАЛІМДЕРДІҢ СҰРАҚТАРЫ -->
        <div id="tab-chat" class="card p-4 mb-4 admin-section shadow-sm">
            <h4 class="text-warning fw-bold mb-3">💬 Мұғалімдердің сұрақтары (Админ жауабы)</h4>
            <div style="max-height: 350px; overflow-y: auto;" class="border p-3 rounded bg-light fw-bold">
                {% for msg in all_messages %}
                    <div class="mb-3 p-3 rounded bg-white border">
                        <small class="text-primary">Мұғалім ID: {{ msg.teacher_id }}</small>
                        <p class="mb-2"><b>Сұрақ:</b> {{ msg.message_text }}</p>
                        {% if msg.admin_reply %}
                            <div class="alert alert-success py-1 mb-0"><b>Жауабыңыз:</b> {{ msg.admin_reply }}</div>
                        {% else %}
                            <form method="POST" action="/admin_reply/{{ msg.id }}">
                                <div class="input-group">
                                    <input type="text" name="reply_text" class="form-control fw-bold" placeholder="Жауапты 1 рет жазу..." required>
                                    <button type="submit" class="btn btn-dark fw-bold">ЖАУАП БЕРУ</button>
                                </div>
                            </form>
                        {% endif %}
                    </div>
                {% else %}
                    <p class="text-muted text-center my-3">Хабарламалар жоқ.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function openAdminTab(sectionId, btnElement) {
            document.querySelectorAll('.admin-section').forEach(sec => sec.classList.remove('active'));
            document.querySelectorAll('.admin-tab-btn').forEach(btn => { btn.classList.remove('active'); });
            document.getElementById(sectionId).classList.add('active');
            btnElement.classList.add('active');
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)