import smtplib, os, datetime, sys, json, logging
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header
from logging.handlers import RotatingFileHandler

smtp_server = ""
smtp_port = 25
smtp_user = "xxx@test.com"
smtp = smtplib.SMTP(host=smtp_server, port=smtp_port)
smtp.set_debuglevel(1)

DEFAULT_RECEIVER_LIST = []

backup_log = "/opt/script/send_mail/runtime.log"
# create logger obj
logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(backup_log, maxBytes=200000, backupCount=2)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
formatter.datefmt = "%Y-%m-%d %H:%M:%S"
logger.addHandler(handler)

def log_msg(msg):
    print(msg)
    logger.info(msg)

def get_last_month():
    #default last month
    today = datetime.datetime.now()
    first = today.replace(day=1)
    date = first - datetime.timedelta(days=1)
    return date.strftime("%Y%m")

#use the json load to enhance the security
data_obj = json.loads(sys.argv[1]) if len(sys.argv) == 2 else {}
log_msg("==========send_health_status==========")
log_msg(data_obj)

#get time
today = datetime.date.today() + datetime.timedelta(0)
today = today.strftime("%Y%m%d")
last_month = get_last_month()
_now_time = datetime.datetime.now()
pre_date = (_now_time + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
current_hour = _now_time.strftime("%Y/%m/%d %H:00")

#check the parameter existed
mail_form = data_obj.get("mail", "null")
log_msg(mail_form)

attach_file = list()
if "attachment" in data_obj:
    attach_file = data_obj.get("attachment", list())
    log_msg(attach_file)
    log_msg(len(attach_file))
    for f in attach_file:
        if not os.path.isfile(f):
            log_msg("file is not existed")
            sys.exit(1)

EMAIL_INFO = {

    "health_status": {
        "title": "系統通知-[XXX] %s XXX報表" % (last_month),
        "recipients": ["abc", "def"],
        "content": "Hi All,\n\n  附檔為 %s 的XXX報表\n\nCY" %(last_month)
    }

}

RECIPIENTS = {
    "abc": "abc@test.com",
    "def": "def@test.com"
}

def make_message():
    today = datetime.date.today().strftime("%Y%m%d")
    subject = EMAIL_INFO.get(mail_form, {}).get("title", "no_subject")
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ",".join([RECIPIENTS[recipient] for recipient in EMAIL_INFO.get(mail_form, {}).get("recipients") if recipient in RECIPIENTS])
    msg["Subject"] = Header(subject, "utf-8")
    text = EMAIL_INFO.get(mail_form, {}).get("content", "no content")
    msg.attach(MIMEText(text, "plain", "utf-8"))
    for f in attach_file:
        #if isinstance(f, unicode):
        #    f = f.encode("utf8")
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name="attachment.file"
            )

        part["Content-Disposition"] = 'attachment; filename="{}"'.format(Header(os.path.basename(f), "utf-8"))
        #filename = Header(os.path.basename(f), "utf-8")
        #part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)
    return msg.as_string()

def make_recv():
    recv = list()

    if len(DEFAULT_RECEIVER_LIST) > 0:
        receiver_list = DEFAULT_RECEIVER_LIST
    else:
        receiver_list = EMAIL_INFO.get(mail_form, {}).get("recipients", [])

    for recipient in receiver_list:
        if not RECIPIENTS.get(recipient):
            continue
        recv.append(RECIPIENTS.get(recipient))
    return recv

if __name__ == "__main__":

    message = make_message()
    recv = make_recv()

    try:
        result = smtp.sendmail(smtp_user, recv, message)

        if len(result) == 0:
            for file in attach_file:
                filename = os.path.basename(file)
                os.remove(filename)
        else:
            log_msg("電子郵件發送失敗，以下是錯誤詳細信息：")
            log_msg(result)

    except smtplib.SMTPException as e:
        log_msg("SMTP發生錯誤，以下是詳細信息：")
        log_msg(e)

    except Exception as e:
        log_msg("發送電子郵件時發生了一些未知錯誤，以下是詳細信息：")
        log_msg(e)

    finally:
        smtp.quit()