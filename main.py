import json
import logging
import os
import random
import string
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import pytz

from functools import wraps

from colorama import Fore, init
from telegram import (
    Bot,
    ChatMember,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.error import NetworkError, TelegramError
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
init(autoreset=True)

md5_game_error = False
usage_count = defaultdict(int)
last_reset_time = defaultdict(lambda: time.time())
mailbox = {}
MAILBOX_FILE = "mailbox.json"
CHECKED_USERS_FILE = "checked_users.txt"
auto_messages = []
QUESTS_FILE = 'quests.json'
user_command_times = defaultdict(list)
md5_game_active = True
md5_bets = {}
md5_timer = 0
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
REF_FILE = 'ref.txt'
accepted_quests = {}
MAX_SELL_SLOTS = 5
TOKEN = "7313527399:AAGt_R-murs5o_s2VAGqDx0tCNH1Zj8kxPw"
API_BOT_2 = "7634067508:AAGiDnpgXp3GqxHctGlOpA_OXQz32Lt7skE"
API_BOT_3 = "7820232504:AAEarJGXYEB-ar-djd_wFQlX3F82nRn682c"
API_BOT_4 = "7542868887:AAHrJfhM2F0KhTcKpm0323LF4UlpW_T1A94"
API_BOT_5 = "7683117642:AAHwZrF7pR944CccZ0w3u3Ul8wpn6KtahNE"
API_BOT_6 = "7048519110:AAFtOkt7MhjFrQvCx8pyW7jUPXYs5gtUIes"
bot_2 = Bot(token=API_BOT_2)
bot_3 = Bot(token=API_BOT_3)
bot_4 = Bot(token=API_BOT_4)
bot_5 = Bot(token=API_BOT_5)
bot_6 = Bot(token=API_BOT_6)
TAIXIU_GROUP_ID = -1002395789623
ROOM_CHECK = -1002424682565
ROOM_CHECK1 = -1002424682565
ROOM_KQ = -1002334717845
taixiu_game_active = False
taixiu_bets = {}
taixiu_timer = 0
recent_results = []
jackpot_amount = {}
user_balances = {}
user_bet_times = {user_id: deque() for user_id in user_balances}
MESSAGE_COUNT_FILE = "message_count.json"
MESSAGE_THRESHOLD = 50
admin_id = 7773778103, 5870603223
ADMIN_ID = 7773778103, 5870603223
MENH_GIA = ['10000', '20000', '50000', '100000', '200000', '500000']
CODES_FILE = "code.txt"
PHIEN_FILE = "phien.txt"
RESULTS_FILE = "kqphientx.txt"
BALANCES_FILE = "sodu.txt"
custom_dice_values = {}
user_bet_times = defaultdict(deque)
TONGCUOC_FILE = "tongcuoc.txt"
SELL_ITEMS_FILE = "sellitems.txt"
INVENTORY_FILE = "inv.txt"
MIN_CUOP_SUCCESS_RATE = 2
MAX_CUOP_SUCCESS_RATE = 15
MIN_BALANCE_REQUIRED = 10000
NOHU = False
LAST_MULTI_TIME = None
executor = ThreadPoolExecutor(max_workers=10)


def notify_usage(func):

    @wraps(func)
    def wrapper(update, context, *args, **kwargs):
        user_id = update.message.from_user.id

        context.bot.send_message(
            chat_id=-1002395789623,
            text=
            f"Thông Báo : <b>WRAPPER</b> : user id [<code>{user_id}</code>] sài 1 hàm của bot",
            parse_mode='html')

        return func(update, context, *args, **kwargs)

    return wrapper


def retry_on_failure(retries=3, delay=5):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except NetworkError as e:
                    print(f"Xảy ra lỗi mạng: {e}. Thử lại sau {delay} giây...")
                    time.sleep(delay)
                except TelegramError as e:
                    print(f"Xảy ra lỗi Telegram: {e}")
                    break
            return None

        return wrapper

    return decorator


@notify_usage
def add_vip_user(update: Update, context: CallbackContext,
                 user_id_to_approve: str):
    try:
        # Kiểm tra nếu update.message tồn tại và là đối tượng Message
        if update.message:
            # Trả lời tin nhắn gốc
            update.message.reply_text(
                f"Người dùng {user_id_to_approve} đã được thêm vào danh sách VIP!"
            )
        else:
            # Gửi tin nhắn trực tiếp nếu không có tin nhắn gốc
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=
                f"Người dùng {user_id_to_approve} đã được thêm vào danh sách VIP!"
            )
    except Exception as e:
        # Xử lý lỗi và ghi log
        error_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
        error_traceback = traceback.format_exc()

        print(f"[{error_time}] Lỗi trong hàm add_vip_user: {e}")
        print(f"Chi tiết lỗi:\n{error_traceback}")

        # Ghi lỗi vào file error.txt
        with open("error.txt", "a", encoding="utf-8") as log_file:
            log_file.write(
                f"[{error_time}] Lỗi trong hàm add_vip_user: {str(e)}\n")
            log_file.write(f"Chi tiết lỗi:\n{error_traceback}\n")


@notify_usage
def add_vip(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        return
    if not update.message:
        return

    try:
        vip_user_id = int(context.args[0])
    except (IndexError, ValueError):
        return

    with open("vip.txt", "a") as vip_file:
        vip_file.write(f"{vip_user_id}\n")

    update.message.reply_text(f"Hoàn Thành {user_id}")


def load_vip_users():
    try:
        with open("vip.txt", "r") as vip_file:
            vip_users = {int(line.strip()) for line in vip_file}
    except FileNotFoundError:
        vip_users = set()
    return vip_users


def load_phien_number():
    try:
        with open(PHIEN_FILE, "r") as file:
            phien_number = int(file.read().strip())
    except FileNotFoundError:
        phien_number = 0
    return phien_number


def save_phien_number(phien_number):
    with open(PHIEN_FILE, "w") as file:
        file.write(str(phien_number))


def read_balances():
    if os.path.exists('sodu.txt'):
        with open('sodu.txt', 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    user_id, balance = parts
                    try:
                        user_balances[int(user_id)] = float(balance)
                    except ValueError:
                        print(f"Invalid balance for user {user_id}: {balance}")


def load_user_balances(filename='sodu.txt'):
    user_balances = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                user_id = int(parts[0])
                balance = float(parts[1])
                user_balances[user_id] = balance
            except ValueError:
                continue
    return user_balances


def save_user_balances():
    with open("sodu.txt", "w") as file:
        for user_id, balance in user_balances.items():
            file.write(f"{user_id} {balance}\n")


def format_currency(amount):
    return f"{int(amount):,} ₫"


def update_user_balance(user_id, amount):
    if user_id in user_balances:
        user_balances[user_id] += amount
    else:
        user_balances[user_id] = amount
    save_user_balances()


def load_recent_results():
    global recent_results
    try:
        with open(RESULTS_FILE, "r") as file:
            lines = file.readlines()
            if len(lines) >= 2:
                recent_results = [line.strip() for line in lines]
            else:
                recent_results = [""] * 2
    except FileNotFoundError:
        recent_results = [""] * 2


def save_recent_results():
    global recent_results
    try:
        with open(RESULTS_FILE, "w") as file:
            for result in recent_results:
                file.write(result + "\n")
    except Exception as e:
        print(f"Error saving recent results: {e}")


def format_recent_results():
    global recent_results
    recent_results_slice = recent_results[-10:]
    formatted_results = []

    for result in recent_results_slice:
        formatted_results.append(result)

    return "".join(formatted_results)

def format_taixiu_results():
    global recent_results_taixiu
    recent_results_slice = recent_results_taixiu[-10:]  # Lấy 10 kết quả gần nhất
    formatted_results = "".join(recent_results_slice)  # Ghép các kết quả thành chuỗi
    return formatted_results if formatted_results else "Chưa có dữ liệu"
    
taixiu_results = []
chanle_results = []

def format_chanle_results():
    global recent_results_chanle
    recent_results_slice = recent_results_chanle[-10:]  # Lấy 10 kết quả gần nhất
    formatted_results = "".join(recent_results_slice)  # Ghép các kết quả thành chuỗi
    return formatted_results if formatted_results else "Chưa có dữ liệu"


def lock_chat(context, chat_id):
    context.bot.set_chat_permissions(chat_id=chat_id,
                                     permissions=ChatPermissions(
                                         can_send_messages=False,
                                         can_invite_users=True))


def unlock_chat(context, chat_id):
    context.bot.set_chat_permissions(chat_id=chat_id,
                                     permissions=ChatPermissions(
                                         can_send_messages=True,
                                         can_invite_users=True))


def save_game_state(phien_number, taixiu_timer, taixiu_bets):
    total_bet_tai = sum(amount for bets in taixiu_bets.values()
                        for choice, amount in bets if choice == 'T')
    total_bet_xiu = sum(amount for bets in taixiu_bets.values()
                        for choice, amount in bets if choice == 'X')
    total_bet_chan = sum(amount for bets in taixiu_bets.values()
                         for choice, amount in bets if choice == 'C')
    total_bet_le = sum(amount for bets in taixiu_bets.values()
                       for choice, amount in bets if choice == 'L')
    with open('cuocphien.txt', 'w') as file:
        file.write(
            f"{phien_number}:{taixiu_timer}:{total_bet_tai}:{total_bet_xiu}:{total_bet_chan}:{total_bet_le}"
        )


def load_game_state():
    try:
        with open('cuocphien.txt', 'r') as file:
            data = file.read().strip().split(':')
            if len(data) == 6:
                phien_number = int(data[0])
                taixiu_timer = int(data[1])
                total_bet_tai = int(data[2])
                total_bet_xiu = int(data[3])
                total_bet_chan = int(data[4])
                total_bet_le = int(data[5])
                return phien_number, taixiu_timer, total_bet_tai, total_bet_xiu, total_bet_chan, total_bet_le
    except FileNotFoundError:
        return None
    except ValueError:
        return None
    return None


def clear_game_state():
    with open('cuocphien.txt', 'w') as file:
        file.write("")


@retry_on_failure(retries=3, delay=5)
def start_taixiu(update: Update, context: CallbackContext):
    global taixiu_game_active, taixiu_bets, taixiu_timer, recent_results, taixiu_betting_active, jackpot_amount, MULTIPLIER, NOHU

    state = load_game_state()
    if state:
        phien_number, taixiu_timer, total_bet_tai, total_bet_xiu, total_bet_chan, total_bet_le = state
    else:
        phien_number = load_phien_number()
        taixiu_timer = 60

    taixiu_betting_active = True
    taixiu_game_active = True
    taixiu_bets = {}
    taixiu_timer = 60
    clear_game_state()

    context.bot.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text=(f"<b>Xin mời đặt cược cho kỳ XX</b> #{phien_number}\n"
              f"<blockquote><b>Cách chơi:</b> T/X/C/L  [Số tiền]</blockquote>\n"
              f"<blockquote>VD: T 50000 / X 50000 / C 50000 / L 50000</blockquote>\n"
              f"<blockquote><b>- Bot trả lời mới được tính là hợp lệ</b>\n"
              f"<b>- Tiền cược tối thiểu 1.000</b>\n"
              f"<b>- Tiền cược tối đa 200.000 mỗi cửa</b></blockquote>\n"
              f"<b>Tất cả người chơi có 60s để cược</b>\n"
              f"<b>- 60s của kỳ XX #{phien_number}</b>\n"),
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Cược Ẩn Danh 👥",
                                 url='https://t.me/F88TAIXIUROOMTELE')
        ]]))

    threading.Thread(target=start_taixiu_timer, args=(update, context)).start()


def nohu_jackpot_amount():
    global MULTIPLIER, jackpot_amount
    try:
        jackpot_amount = load_jackpot_amount()
        new_jackpot_amount = jackpot_amount * MULTIPLIER
        save_jackpot_amount(new_jackpot_amount)
        return new_jackpot_amount
    except (FileNotFoundError, ValueError) as e:
        print(f"Error reading or processing the jackpot file: {e}")
        return None


def nonohu_jackpot_amount():
    global MULTIPLIER, jackpot_amount
    try:
        jackpot_amount = load_jackpot_amount()
        new_jackpot_amount = jackpot_amount / MULTIPLIER
        save_jackpot_amount(new_jackpot_amount)
        return new_jackpot_amount
    except (FileNotFoundError, ValueError) as e:
        print(f"Error reading or processing the jackpot file: {e}")
        return None


def save_jackpot_amount(jackpot_amount):
    with open('jackpot.txt', 'w') as file:
        file.write(str(jackpot_amount))


def load_jackpot_amount():
    if os.path.exists('jackpot.txt'):
        with open('jackpot.txt', 'r') as file:
            return float(file.read())
    return 30000


@retry_on_failure(retries=3, delay=5)
def start_taixiu_timer(update: Update, context: CallbackContext):
    global taixiu_timer, taixiu_betting_active, jackpot_amount
    jackpot_amount = load_jackpot_amount()
    while taixiu_timer > 0:
        time.sleep(1)
        taixiu_timer -= 1
        if taixiu_timer % 20 == 0:
            keyboard = [[
                InlineKeyboardButton("Xem Cầu",
                                     url='https://t.me/+g3wLnlV8qKM2ZTI1')
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            phien_number = load_phien_number()
            # Tính tổng cược Tài và Xỉu
            total_bet_tai = sum(amount for bets in taixiu_bets.values()
                                for choice, amount in bets if choice == 'T')
            total_bet_xiu = sum(amount for bets in taixiu_bets.values()
                                for choice, amount in bets if choice == 'X')

            # Tính tổng cược Chẵn và Lẻ
            total_bet_chan = sum(amount for bets in taixiu_bets.values()
                                 for choice, amount in bets if choice == 'C')
            total_bet_le = sum(amount for bets in taixiu_bets.values()
                               for choice, amount in bets if choice == 'L')

            # Hàm định dạng số
            def format_number(value):
                """Định dạng số với dấu chấm phân cách hàng nghìn."""
                if value == 0:
                    return "0"  # Đảm bảo nếu là 0, không có dấu phân cách.
                return f"{value:,.0f}".replace(",", ".")

            # Tạo tin nhắn
            message = (
                f"<b>Còn {taixiu_timer}s để cược kỳ XX #{phien_number}\n"
                f"🔵TÀI : {format_number(total_bet_tai)}\n"
                f"🔴XỈU : {format_number(total_bet_xiu)}\n\n"  # Khoảng cách giữa các phần
                f"⚪️CHẴN: {format_number(total_bet_chan)}\n"
                f"⚫️LẺ  : {format_number(total_bet_le)}</b>")

            # Gửi tin nhắn với định dạng HTML
            context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                     text=message,
                                     reply_markup=reply_markup,
                                     parse_mode='HTML')

            save_game_state(phien_number, taixiu_timer, taixiu_bets)

    phien_number = load_phien_number()
    taixiu_betting_active = False
    lock_chat(context, TAIXIU_GROUP_ID)
    bot_4.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text=
        (f"HẾT THỜI GIAN CƯỢC CỬA\n"
         f"<blockquote>💥Bắt đầu tung XX kỳ <b>#{phien_number}</b>💥</blockquote>\n"
         ),
        parse_mode='HTML',
    )
    generate_taixiu_result(update, context)


def update_bet_amount(user_id, bet_amount):
    bets = {}

    if os.path.exists("tongcuoc.txt"):
        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                line_user_id = int(float(line_user_id))
                bets[line_user_id] = float(line_bet_amount)

    user_id = int(float(user_id))
    if user_id in bets:
        current_bet_amount = bets[user_id]
        updated_bet_amount = current_bet_amount + bet_amount
        bets[user_id] = updated_bet_amount
    else:
        bets[user_id] = bet_amount

    # Write the updated contents back to the file
    with open("tongcuoc.txt", "w") as file:
        for line_user_id, line_bet_amount in bets.items():
            file.write(f"{line_user_id} {line_bet_amount}\n")


def get_today_bets(user_id):
    bets = {}
    if os.path.exists("tongcuoc.txt"):
        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                line_user_id = int(float(line_user_id))  # Convert to integer
                bets[line_user_id] = float(line_bet_amount)  # Store as float

    user_id = int(float(user_id))
    return bets.get(user_id, 0)


def rut(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    message = ("Lựa Chọn Ngân Hàng Rút")

    keyboard = [["🏧 Rút Bank", "💳 Rút Momo"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    if chat_id - 1002267592304:
        return
    else:
        update.message.reply_text(message,
                                  parse_mode='HTML',
                                  reply_markup=reply_markup)


def xlymomo(update: Update, context: CallbackContext):

    message = (
        "<b>💸 RÚT TIỀN MOMO </b>\n\n"
        "💸 Vui lòng thực hiện theo hướng dẫn sau:\n\n"
        "/rutmomo [SĐT] [Số tiền muốn rút]\n"
        "➡️ VD: /rutmomo 0987112233 200000\n\n"
        "⚠️ Lưu ý: ❌ Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.\n"
        "❗️ Phí rút tiền: 5.900đ cho các giao dịch dưới 50.000đ. (RÚT TỪ 50.000đ TRỞ LÊN KHÔNG MẤT PHÍ RÚT)\n\n\n"
        "ĐỂ RÚT TỐI THIỂU MOMO LÀ 50.000 VND / BANK LÀ 100.000 VND\n\n")
    update.message.reply_text(message, parse_mode='HTML')


def xlybank(update: Update, context: CallbackContext):

    message = (
        "🏧 Vui lòng thực hiện theo hướng dẫn sau:\n\n"
        "👉 /rutbank [Số tiền muốn rút] [Mã ngân hàng] [Số tài khoản] [Tên chủ tài khoản]\n"
        "👉 VD: /rutbank 100000 VCB 01234567890 NGUYEN VAN A\n\n"
        "⚠️ Lưu ý: Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin Tài khoản.\n\n"
        "<b>MÃ NGÂN HÀNG - TÊN NGÂN HÀNG</b>\n\n"
        "📌 ACB ==> ACB - NH TMCP A CHAU\n"
        "📌 BIDV ==> BIDV - NH DAU TU VA PHAT TRIEN VIET NAM\n"
        "📌 MBB ==> MB - NH TMCP QUAN DOI\n"
        "📌 MSB ==> MSB - NH TMCP HANG HAI\n"
        "📌 TCB ==> TECHCOMBANK - NH TMCP KY THUONG VIET NAM\n"
        "📌 TPB ==> TPBANK - NH TMCP TIEN PHONG\n"
        "📌 VCB ==> VIETCOMBANK - NH TMCP NGOAI THUONG VIET NAM\n"
        "📌 VIB ==> VIB - NH TMCP QUOC TE VIET NAM\n"
        "📌 VPB ==> VPBANK - NH TMCP VIET NAM THINH VUONG\n"
        "📌 VTB ==> VIETINBANK - NH TMCP CONG THUONG VIET NAM\n"
        "📌 SHIB ==> SHINHANBANK - NH TNHH SHINHAN VIET NAM\n"
        "📌 ABB ==> ABBANK - NH TMCP AN BINH\n"
        "📌 AGR ==> AGRIBANK - NH NN & PTNT VIET NAM\n"
        "📌 VCCB ==> BANVIET - NH TMCP BAN VIET\n"
        "📌 BVB ==> BAOVIETBANK - NH TMCP BAO VIET (BVB)\n"
        "📌 DAB ==> DONGABANK - NH TMCP DONG A\n"
        "📌 EIB ==> EXIMBANK - NH TMCP XUAT NHAP KHAU VIET NAM\n"
        "📌 GPB ==> GPBANK - NH TMCP DAU KHI TOAN CAU\n"
        "📌 HDB ==> HDBANK - NH TMCP PHAT TRIEN TP.HCM\n"
        "📌 KLB ==> KIENLONGBANK - NH TMCP KIEN LONG\n"
        "📌 NAB ==> NAMABANK - NH TMCP NAM A\n"
        "📌 NCB ==> NCB - NH TMCP QUOC DAN\n"
        "📌 OCB ==> OCB - NH TMCP PHUONG DONG\n"
        "📌 OJB ==> OCEANBANK - NH TMCP DAI DUONG (OJB)\n"
        "📌 PGB ==> PGBANK - NH TMCP XANG DAU PETROLIMEX\n"
        "📌 PVB ==> PVCOMBANK - NH TMCP DAI CHUNG VIET NAM\n"
        "📌 STB ==> SACOMBANK - NH TMCP SAI GON THUONG TIN\n"
        "📌 SGB ==> SAIGONBANK - NH TMCP SAI GON CONG THUONG\n"
        "📌 SCB ==> SCB - NH TMCP SAI GON\n"
        "📌 SAB ==> SEABANK - NH TMCP DONG NAM A\n"
        "📌 SHB ==> SHB - NH TMCP SAI GON HA NOI\n\n"
        "ĐỂ RÚT TỐI THIỂU MOMO LÀ 50.000 VND / BANK LÀ 100.000 VND\n\n")
    update.message.reply_text(message, parse_mode='HTML')


def rutmomo(update: Update, context: CallbackContext):
    global vip_users, user_balances
    user_id = update.message.from_user.id
    message_text = update.message.text.split()

    vip_user = load_vip_users()

    # Kiểm tra cú pháp
    if len(message_text) != 3:
        update.message.reply_text(
            "Lệnh không hợp lệ! Vui lòng nhập /rutmomo [SĐT] [Số tiền muốn rút]"
        )
        return

    phone_number = message_text[1]
    amount_str = message_text[2]

    try:
        amount = int(amount_str)
    except ValueError:
        update.message.reply_text("Vui lòng nhập số tiền hợp lệ.")
        return

    if user_id not in vip_user:
        total_code_amount = 0
        with open('tanthucode.txt', 'r') as file:
            for line in file:
                uid, value = line.strip().split()
                if str(user_id) == uid:
                    total_code_amount += int(float(value))

        if total_code_amount > 30000:
            update.message.reply_text(
                "<b>[ TÂN THỦ ]</b> Bạn đã nhập tổng thực nhận code trên 30.000 VND. Không thể rút tiền.",
                parse_mode='HTML')
            return

        # Kiểm tra nếu user đã rút tiền trước đó
        with open('tanthu_rut.txt', 'r') as file:
            previous_withdrawals = file.read().splitlines()
        if str(user_id) in previous_withdrawals:
            update.message.reply_text(
                "Bạn đã rút tiền trước đó. Vui lòng nạp để thoát tân thủ.")
            return

        if amount != 50000:
            update.message.reply_text(
                "❌ LƯU Ý : Tân thủ chỉ có thể rút đúng 50,000 VND, với số tiền thực nhận là 10,000 VND."
            )
            return

        user_balances[user_id] = 0
        with open('tanthu_rut.txt', 'a') as file:
            file.write(f"{user_id}\n")

        message = (
            f"<b>💸 RÚT TIỀN QUA MOMO</b>\n\n"
            f"🔹 Số điện thoại: {phone_number}\n"
            f"🔹 Số tiền rút: {format_currency(amount)}\n"
            f"🔹 Số tiền thực nhận: 10,000 VND\n\n"
            "⚠️ Lưu ý: Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.")
        update.message.reply_text(message, parse_mode='HTML')
        context.bot.send_message(
            chat_id=ROOM_CHECK1,
            text=f"User {user_id} yêu cầu rút tiền MOMO (tân thủ)")

        admin_id = 5870603223
        context.bot.send_message(
            chat_id=admin_id,
            text=
            f"💵 Yêu cầu rút MOMO (tân thủ) 💵\nUSER ID {user_id}\nSĐT: {phone_number}\nSố tiền yêu cầu: {amount} VND\nThực nhận: 10,000 VND"
        )
        return

    load_user_balances()
    fee = 5900 if amount < 50000 else 0

    if user_id in user_balances:
        if user_balances[user_id] >= amount + fee:
            user_balances[user_id] -= (amount + fee)
        else:
            update.message.reply_text("Số dư không đủ để thực hiện giao dịch.")
            return

    # Thông báo giao dịch cho VIP user
    message = (
        f"<b>💸 RÚT TIỀN QUA MOMO</b>\n\n"
        f"🔹 Số điện thoại: {phone_number}\n"
        f"🔹 Số tiền rút: {format_currency(amount)}\n"
        f"🔹 Phí rút tiền: {fee} VND\n\n"
        "⚠️ Lưu ý: Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.")
    update.message.reply_text(message, parse_mode='HTML')
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} yêu cầu rút tiền MOMO")

    # Thông báo đến admin cho VIP user
    admin_id = 5870603223
    context.bot.send_message(
        chat_id=admin_id,
        text=
        f"💵 Yêu cầu rút MOMO 💵\nUSER ID {user_id}\nSĐT: {phone_number}\nSố tiền: {amount} VND\nPhí: {fee} VND"
    )


def notiall(update: Update, context: CallbackContext):
    admin_id = 5870603223
    user_id = update.message.from_user.id
    message_text = update.message.text.split(maxsplit=2)

    # Kiểm tra xem người gửi có phải là admin không
    if user_id != admin_id:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    # Kiểm tra cú pháp lệnh
    if len(message_text) < 2:
        update.message.reply_text(
            "Lệnh không hợp lệ! Vui lòng nhập /notiall [bold] {NỘI DUNG}")
        return

    # Kiểm tra nếu tin nhắn in đậm
    is_bold = message_text[1].lower() == "bold"
    content = message_text[2] if is_bold else message_text[1]

    # Đọc danh sách user từ file `sodu.txt`
    try:
        with open("sodu.txt", "r") as file:
            user_ids = [line.split()[0] for line in file]
    except FileNotFoundError:
        update.message.reply_text("File sodu.txt không tồn tại.")
        return

    # Gửi tin nhắn cho từng user
    for uid in user_ids:
        try:
            if is_bold:
                context.bot.send_message(chat_id=int(uid),
                                         text=f"<b>{content}</b>",
                                         parse_mode="HTML")
            else:
                context.bot.send_message(chat_id=int(uid), text=content)
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn đến user {uid}: {e}")

    update.message.reply_text("Đã gửi tin nhắn đến tất cả người dùng.")


def rutbank(update: Update, context: CallbackContext):
    global vip_users, user_balances
    user_id = update.message.from_user.id
    message_text = update.message.text.split()

    vip_user = load_vip_users()
    load_user_balances()

    if user_id != 5870603223:
        mess = "Bảo trì rút banking"
        context.bot.send_message(chat_id=user_id, text=mess)
        return

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng lệnh /rutbank")
        return

    # Kiểm tra cú pháp
    if len(message_text) < 5:
        update.message.reply_text(
            "Lệnh không hợp lệ! Vui lòng nhập /rutbank [Số tiền] [Mã ngân hàng] [Số tài khoản] [Tên chủ tài khoản]"
        )
        return

    amount_str = message_text[1]
    bank_code = message_text[2].upper()
    account_number = message_text[3]
    account_holder = " ".join(message_text[4:])

    try:
        amount = int(amount_str)
    except ValueError:
        update.message.reply_text("Vui lòng nhập số tiền hợp lệ.")
        return

    # Kiểm tra giới hạn rút cho tân thủ
    if user_id not in vip_user and amount > 10000:
        update.message.reply_text(
            "❌ Tân Thủ Rút Tối Đa 10.000 VND [ CHỈ VỀ MOMO ]")
        return

    if user_id in user_balances:
        if user_balances[user_id] >= amount:
            user_balances[user_id] -= amount
        else:
            update.message.reply_text("Số dư không đủ để thực hiện giao dịch.")

    # Tạo thông báo rút tiền qua BANK
    message = (
        f"<b>💸 RÚT TIỀN QUA BANK</b>\n\n"
        f"🔹 Ngân hàng: {bank_code}\n"
        f"🔹 Số tài khoản: {account_number}\n"
        f"🔹 Chủ tài khoản: {account_holder}\n"
        f"🔹 Số tiền rút: {format_currency(amount)} VND\n\n"
        "⚠️ Lưu ý: Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin Tài khoản."
    )
    update.message.reply_text(message, parse_mode='HTML')
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} yêu cầu rút tiền BANK")

    # Thông báo cho admin
    admin_id = 5870603223
    context.bot.send_message(
        chat_id=admin_id,
        text=
        f"💵 Yêu cầu rút BANK 💵\nUSER ID {user_id}\nNgân hàng: {bank_code}\nSố tài khoản: {account_number}\n"
        f"Chủ tài khoản: {account_holder}\nSố tiền: {format_currency(amount)} VND"
    )


def taixiu_bet(update: Update, context: CallbackContext):
    global taixiu_bets, taixiu_game_active, taixiu_timer, jackpot_amount, user_balances, taixiu_betting_active

    if not update.message:
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    chat_id = update.message.chat_id
    is_private = chat_id == user_id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return

    message_text = update.message.text.strip().split()
    if len(message_text) != 2:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Vui lòng nhập theo định dạng:\n👉 [T/X/C/L] [số tiền cược]")
        return

    choice = message_text[0].upper()
    bet_amount_str = message_text[1].lower()

    if choice not in ['T', 'X', 'C', 'L']:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="🚫 <b>Sai Cửa Cược</b>",
                                 parse_mode='HTML')
        return

    if bet_amount_str == 'max':
        bet_amount = min(user_balances.get(user_id, 0), 300000)
    else:
        try:
            bet_amount = int(bet_amount_str)
        except ValueError:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="🚫 <b>Số tiền cược không hợp lệ</b>",
                                     parse_mode='HTML')
            return

    if bet_amount <= 0:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="🚫 <b>Số tiền cược không hợp lệ</b>",
                                 parse_mode='HTML')
        return

    if taixiu_game_active:
        if not taixiu_game_active or taixiu_timer <= 1 or taixiu_timer > 60:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>🚫 Không trong thời gian nhận cược</b>",
                parse_mode='HTML')
            return

        if bet_amount <= 999:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="❌ Cược tối thiểu <b>1,000 VND</b>",
                                     parse_mode='HTML')
            return
        MAX_BET_LIMIT = 300000  # Giới hạn cược tối đa

        if bet_amount > MAX_BET_LIMIT:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Cược tối đa là <b>{MAX_BET_LIMIT:,} VND</b>",
                parse_mode='HTML')
            return

        if user_balances.get(user_id, 0) < bet_amount:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>❌ Số dư không đủ để đặt cược</b>",
                parse_mode='HTML')
            return

        if user_id not in taixiu_bets:
            taixiu_bets[user_id] = []

        # Kiểm tra cược Tài/Xỉu hoặc Chẵn/Lẻ
        if choice in ['T', 'X']:
            existing_bets = [
                bet for bet in taixiu_bets[user_id]
                if bet[0] in ['T', 'X'] and bet[0] != choice
            ]
        elif choice in ['C', 'L']:
            existing_bets = [
                bet for bet in taixiu_bets[user_id]
                if bet[0] in ['C', 'L'] and bet[0] != choice
            ]

        if existing_bets:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Bạn chỉ được đặt cược 1 cửa T/X hoặc C/L trong phiên.",
                parse_mode='HTML')
            return

        # Thêm cược vào cửa đã chọn
        taixiu_bets[user_id].append((choice, bet_amount))
        user_balances[user_id] -= bet_amount

        update_bet_amount(user_id, bet_amount)
        save_jackpot_amount(jackpot_amount)

        if is_private:
            bet_success_message = (
                f"✅ <b>Cược ẨN DANH thành công {format_currency(bet_amount)} vào cửa {'Chẵn ⚪️' if choice == 'C' else 'Lẻ ⚫️' if choice == 'L' else 'XỈU 🔴' if choice == 'X' else 'TÀI 🔵'}</b>\n"
                f"💳 <b>Số dư hiện tại :</b> {format_currency(user_balances[user_id])}"
            )
            update.message.reply_text(bet_success_message, parse_mode='HTML')
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=
                f"🏆 <b>Cược ẨN DANH thành công {format_currency(bet_amount)} vào cửa {'Chẵn ⚪️' if choice == 'C' else 'Lẻ ⚫️' if choice == 'L' else 'XỈU 🔴' if choice == 'X' else 'TÀI 🔵'}</b>",
                parse_mode='HTML')
        else:
            bet_success_message = (
                f"✅ <b>Cược thành công {format_currency(bet_amount)} vào cửa {'Chẵn ⚪️' if choice == 'C' else 'Lẻ ⚫️' if choice == 'L' else 'XỈU 🔴' if choice == 'X' else 'TÀI 🔵'}</b>"
            )
            update.message.reply_text(bet_success_message, parse_mode='HTML')
            private_message = (
                f"🍀 <b>Cược thành công {format_currency(bet_amount)} vào cửa {'Chẵn ⚪️' if choice == 'C' else 'Lẻ ⚫️' if choice == 'L' else 'XỈU 🔴' if choice == 'X' else 'TÀI 🔵'}</b>\n"
                f"💳 <b>Số dư hiện tại :</b> {format_currency(user_balances[user_id])}"
            )
            context.bot.send_message(chat_id=user_id,
                                     text=private_message,
                                     parse_mode='HTML')

        save_game_state(load_phien_number(), taixiu_timer, taixiu_bets)
        
def payout_winners(update: Update, context: CallbackContext, result_taixiu, result_chanle):
    global taixiu_bets, user_balances, jackpot_amount

    total_win_amount = 0
    total_lose_amount = 0

    # Duyệt qua tất cả người chơi và cược
    for user_id, bets in taixiu_bets.items():
        user_win_amount = 0
        user_lose_amount = 0
        win_message = []
        lose_message = []

        # Tính toán thắng/thua cho từng cửa cược
        for choice, amount in bets:
            # Lấy số phiên (kỳ XX)
            phien_number = load_phien_number()  # Giả sử đây là hàm lấy số phiên

            if choice == result_taixiu or choice == result_chanle:
                win_amount = amount * 1.95
                user_win_amount += win_amount
                win_message.append(
                    f"✅ Kỳ XX: {phien_number} Thắng Room\n {choice} {amount:,}\n Tiền thắng: {win_amount:,}"
                )
            else:
                user_lose_amount += amount
                lose_message.append(
                    f"❌ Kỳ XX: {phien_number} Thua Room {choice} {amount:,}\n Tiền thua: {amount:,}"
                )

        # Cập nhật tổng tiền thắng và thua
        total_win_amount += user_win_amount
        total_lose_amount += user_lose_amount

        # Cập nhật số dư người chơi
        user_balances[user_id] = user_balances.get(user_id, 0) + user_win_amount
        save_user_balances()  # Lưu lại số dư vào file (nếu hàm này có sẵn)

        # Cập nhật chuỗi thắng/thua
        if user_win_amount > 0:
            winning_streaks[user_id] = winning_streaks.get(user_id, 0) + 1
            losing_streaks[user_id] = 0
        else:
            losing_streaks[user_id] = losing_streaks.get(user_id, 0) + 1
            winning_streaks[user_id] = 0

        # Gửi thông báo kết quả cho người chơi
        if win_message:
            result_message_win = "\n".join(win_message)
            result_message_win += f"\n🎫 Số dư hiện tại: {user_balances[user_id]:,}"
            context.bot.send_message(chat_id=user_id, text=result_message_win, parse_mode="HTML")

        if lose_message:
            result_message_lose = "\n".join(lose_message)
            result_message_lose += f"\n🎫 Số dư hiện tại: {user_balances[user_id]:,}"
            context.bot.send_message(chat_id=user_id, text=result_message_lose, parse_mode="HTML")
    # Trả về tổng tiền thắng và thua của cả phiên
    return total_win_amount, total_lose_amount





def save_streaks(filename, streaks):
    with open(filename, "w") as file:
        for user_id, streak in streaks.items():
            file.write(f"{user_id} {streak}\n")


def load_streaks(filename):
    streaks = {}
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                user_id, streak = line.strip().split()
                streaks[int(user_id)] = int(streak)
    return streaks


def save_streaks(filename, streaks):
    with open(filename, "w") as file:
        for user_id, streak in streaks.items():
            file.write(f"{user_id} {streak}\n")


def load_streaks(filename):
    streaks = {}
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                user_id, streak = line.strip().split()
                streaks[int(user_id)] = int(streak)
    return streaks


def reset_jackpot_amount():
    with open('jackpot.txt', 'w') as f:
        f.write('0')
# Thêm biến toàn cục để lưu lịch sử Tài/Xỉu và Chẵn/Lẻ
recent_results_taixiu = []
recent_results_chanle = []

# Hàm lưu kết quả Tài/Xỉu
def save_taixiu_results():
    global recent_results_taixiu
    with open("kq_taixiu.txt", "w") as file:
        for result in recent_results_taixiu:
            file.write(result + "\n")

# Hàm tải kết quả Tài/Xỉu
def load_taixiu_results():
    global recent_results_taixiu
    try:
        with open("kq_taixiu.txt", "r") as file:
            recent_results_taixiu = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        recent_results_taixiu = []

# Hàm lưu kết quả Chẵn/Lẻ
def save_chanle_results():
    global recent_results_chanle
    with open("kq_chanle.txt", "w") as file:
        for result in recent_results_chanle:
            file.write(result + "\n")

# Hàm tải kết quả Chẵn/Lẻ
def load_chanle_results():
    global recent_results_chanle
    try:
        with open("kq_chanle.txt", "r") as file:
            recent_results_chanle = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        recent_results_chanle = []
        
@retry_on_failure(retries=3, delay=5)
def generate_taixiu_result(update: Update, context: CallbackContext):
    global taixiu_game_active, taixiu_bets, jackpot_amount, recent_results, user_balances, NOHU, MULTIPLIER, winning_streaks, losing_streaks

    if not taixiu_game_active:
        return

    if random.random() < 1.00:
        dice1 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value
        time.sleep(0)
        dice2 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value
        time.sleep(0)
        dice3 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value
    else:
        time.sleep(random.uniform(0, 1))
        dice1 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value

        if dice1 in [1, 6]:
            time.sleep(2)

        time.sleep(random.uniform(1, 1.05))
        dice2 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value

        total = dice1 + dice2

        if total in [2, 3, 4, 10, 11, 12]:
            dice3 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value
        else:
            time.sleep(2)
            dice3 = bot_2.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value

    time.sleep(random.uniform(0, 0.05))
    dice_values = [dice1, dice2, dice3]
    # Tính tổng điểm từ ba xúc xắc
    total = sum(dice_values)

    # Xử lý kết quả Chẵn/Lẻ
    if total % 2 == 0:  # Chẵn
        chan_le_result = 'C'
        chan_le_emoji = "⚪️"
    else:  # Lẻ
        chan_le_result = 'L'
        chan_le_emoji = "⚫️"

    # Cập nhật danh sách Chẵn/Lẻ
    recent_results_chanle.append(chan_le_emoji)
    if len(recent_results_chanle) > 10:
        recent_results_chanle.pop(0)
    save_chanle_results()  # Lưu kết quả Chẵn/Lẻ vào file

    total_win_amount = 0
    total_lose_amount = 0
    
    phien_number = load_phien_number()

    if total == 3 or total == 18:
        result = "X" if total == 3 else "T"
        result_emoji = "🟡"
        recent_results.append(result_emoji)
        save_recent_results()

        total_bet_amount = sum(amount for user_id, bets in taixiu_bets.items()
                               for choice, amount in bets if choice == result)
        top_bettors = []

        for user_id, bets in taixiu_bets.items():
            for choice, amount in bets:
                if choice == result:
                    payout = (amount / total_bet_amount) * jackpot_amount
                    total_payout = payout + amount * 1.95
                    update_user_balance(user_id, total_payout)
                    top_bettors.append((user_id, amount, total_payout))

                    context.bot.send_message(
                        chat_id=user_id,
                        text=
                        f"🎉 <b>Thắng Nổ Hũ Kỳ XX{phien_number}</b>: {format_currency(payout)}\n",
                        parse_mode='HTML')

        context.bot.send_message(
            chat_id=ROOM_CHECK, text=f"Nổ hũ Room {dice1} - {dice2} - {dice3}")

        try:
            result_message = f"<b>🔥 Nổ Hũ Kỳ XX{phien_number}</b>\n\n"
            result_message += f"<b>Kết Quả {dice1} - {dice2} - {dice3}</b>\n\n"
            result_message += "<b>👉 ID Top - Tiền Cược - Tổng Thắng</b>\n"
            for user_id, bet_amount, payout in top_bettors:
                result_message += f"<a href='tg://user?id={user_id}'>{user_id}</a> - {format_currency(bet_amount)} - {format_currency(payout)}\n"

            pinned_message = context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                                      text=result_message,
                                                      parse_mode='HTML')
            context.bot.pin_chat_message(chat_id=TAIXIU_GROUP_ID,
                                         message_id=pinned_message.message_id,
                                         disable_notification=True)
            context.bot.send_message(
                chat_id=ROOM_KQ,
                text=(
                   f"<b>NỔ HŨ XÚC XẮC phiên #{phien_number}</b>\n"
                   f"<b> {dice1} {dice2} {dice3} ({total}) "
                   f"{'XỈU' if result == 'X' else 'TÀI'} "
                   f"{'CHẴN' if chan_le_result == 'C' else 'LẺ'} "
                   f"{'🔴' if result == 'X' else '🔵'} "
                   f"{'⚪️' if chan_le_result == 'C' else '⚫️'}</b>\n"
                   f"<blockquote><b>Kết quả 10 cầu gần nhất:</b>\n\n"
                   f"{format_taixiu_results()}\n\n"
                   f"{format_chanle_results()}\n</blockquote>"
                ),
                parse_mode='HTML')
        except Exception as e:
            logging.error(f"Failed to send new game message: {e}")

        reset_jackpot_amount()
        taixiu_game_active = False
        clear_game_state()

        try:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=("🎲 Phiên Tiếp Theo Sẽ Bắt Đầu Trong Giây Lát 🎲"),
            )
            unlock_chat(context, TAIXIU_GROUP_ID)
            increment_phien_number()
            time.sleep(3)
            start_taixiu(update, context)
        except Exception as e:
            logging.error(f"Failed to send new game message: {e}")

    else:
        if total >= 11:
            result = "T"
            result_emoji = "🔵"
        else:
            result = "X"
            result_emoji = "🔴"

        recent_results_taixiu.append(result_emoji)
        if len(recent_results_taixiu) > 10:
            recent_results_taixiu.pop(0)
        save_taixiu_results()  # Lưu kết quả Tài/Xỉu vào file

        # Cộng tiền thua vào hũ nếu cần
        if isinstance(jackpot_amount, (int, float)):
            if total_lose_amount > total_win_amount/ 1.95:
                amount_add_to_jackpot = total_lose_amount * 0.05
                jackpot_amount += amount_add_to_jackpot
            else:
                amount_add_to_jackpot = 0
        save_jackpot_amount(jackpot_amount)

        # Lưu lịch sử kết quả chẵn/lẻ
        recent_results.append(chan_le_emoji)
        if len(recent_results) > 10:
            recent_results.pop(0)
        save_recent_results()

        phien_number = load_phien_number()

        try:
            # Tính kết quả Tài/Xỉu và Chẵn/Lẻ
            result_taixiu = 'T' if total >= 11 else 'X'  # Tài hoặc Xỉu
            result_chanle = 'C' if total % 2 == 0 else 'L'  # Chẵn hoặc Lẻ

            # Gọi hàm payout_winners với các giá trị đã tính
            total_win_amount, total_lose_amount = payout_winners(update, context, result_taixiu, result_chanle)

            if isinstance(jackpot_amount, (int, float)):
                # Chỉ cộng vào hũ khi tổng tiền thua cao hơn tổng tiền thắng
                if total_lose_amount > total_win_amount/ 1.95:
                    amount_add_to_jackpot = total_lose_amount * 0.05
                    jackpot_amount += amount_add_to_jackpot
                else:
                    amount_add_to_jackpot = 0  # Không cộng thêm vào hũ
            save_jackpot_amount(jackpot_amount)

            # Tạo chuỗi thông báo hũ hiện tại
            if amount_add_to_jackpot > 0:
                jackpot_message = f"<b>┃</b> Hũ hiện tại: <b>{format_currency(jackpot_amount)} (+{format_currency(amount_add_to_jackpot)})</b>\n"
            else:
                jackpot_message = f"<b>┃</b> Hũ hiện tại: <b>{format_currency(jackpot_amount)}</b>\n"

            # Gửi tin nhắn kết quả
            keyboard = [[
                InlineKeyboardButton("Nạp Tiền Tại Đây 💵",
                                     url='https://t.me/botTX1_bot?start=nap')
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=(
                    f"<b>KẾT QUẢ XX KỲ #{phien_number}</b>\n"
                    f"<b>┏━━━━━━━━━━━━━━━━┓</b>\n"
                    f"<b>┃ {dice1} {dice2} {dice3} ({total}) "
                    f"{'XỈU' if result == 'X' else 'TÀI'} "
                    f"{'CHẴN' if chan_le_result == 'C' else 'LẺ'} "
                    f"{'🔴' if result == 'X' else '🔵'} "
                    f"{'⚪️' if chan_le_result == 'C' else '⚫️'}</b>\n"
                    f"<b>┃</b>\n"
                    f"<b>┃</b> Tổng thắng: <b>{format_currency(total_win_amount/ 1.95)}</b>\n"
                    f"<b>┃</b> Tổng thua: <b>{format_currency(total_lose_amount)}</b>\n"
                    f"<b>┃</b>\n"
                    f"<b>┃</b> Hũ: <b>{format_currency(jackpot_amount)}"
                    f"(+{format_currency(amount_add_to_jackpot)})</b>\n"
                    f"<b>┗━━━━━━━━━━━━━━━━┛</b>\n"
                    f"\n"
                    f"<blockquote><b>Kết quả 10 cầu gần nhất:</b>\n\n"
                    f"{format_taixiu_results()}\n\n"
                    f"{format_chanle_results()}\n</blockquote>"
                ),
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send result message: {e}")

        context.bot.send_message(
            chat_id=ROOM_KQ,
            text=(
                f"<pre>"
                f"KỲ #{phien_number:<5} "
                f"{dice1:<2} {dice2:<2} {dice3:<2} "
                f"({total:<3}) "
                f"{'XỈU' if result == 'X' else 'TÀI':<5} "
                f"{'CHẴN' if chan_le_result == 'C' else 'LẺ':<6} "
                f"{'🔴' if result == 'X' else '🔵':<3} "
                f"{'⚪️' if chan_le_result == 'C' else '⚫️':<3}"
                f"</pre>"
            ),
            parse_mode='HTML'
        )

        # Kết thúc phiên chơi
        taixiu_game_active = False
        clear_game_state()

        unlock_chat(context, TAIXIU_GROUP_ID)
        increment_phien_number()
        time.sleep(3)
        start_taixiu(update, context)


def approve_deposit(update: Update, context: CallbackContext):
    admin_ids = {5870603223}
    if update.message.from_user.id not in admin_ids:
        update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return

    args = context.args
    if len(args) != 2:
        update.message.reply_text(
            "❌ Sai cú pháp! Vui lòng sử dụng: /duyetnap [Số Tiền] [ID USER]")
        return

    amount = float(args[0])
    user_id = int(args[1])

    ref_dict = read_ref_file()

    if user_id not in ref_dict:
        update.message.reply_text(
            f"❌ User {user_id} chưa sử dụng link mời nào.")

    inviter_id = ref_dict[user_id]

    if inviter_id == -1:
        update.message.reply_text(
            f"❌ User {user_id} không có người mời để nhận hoa hồng.")

    commission_percentage = random.randint(5, 10)
    commission = amount * commission_percentage / 100

    context.bot.send_message(
        chat_id=inviter_id,
        text=
        f"Bạn nhận được {format_currency(commission)} từ {commission_percentage}% tiền hoa hồng nạp của đệ tử {user_id}."
    )

    update.message.reply_text(
        f"✅ Đã duyệt nạp tiền {format_currency(amount)} cho ID {user_id} và cộng hoa hồng {format_currency(commission)} cho người mời."
    )


def nap(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Kiểm tra nếu người dùng bị cấm
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    # Tin nhắn thông báo các kênh nạp
    message = ("<b>🏛 CÁC KÊNH NẠP</b>\n\n"
               "<b>☘️ MOMO</b> : /momo [ Số Tiền Nạp ]\n"
               "<b>🌟 BANKING</b> : /bank [ Số Tiền Nạp ]\n"
               "<b>⚡️ THẺ CÀO</b> : /napthe")
    update.message.reply_text(message, parse_mode='HTML')
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


def momo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_text = update.message.text.split()

    # Kiểm tra nếu người dùng bị cấm
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    # Kiểm tra đầu vào
    if len(message_text) != 2:
        update.message.reply_text(
            "Lệnh không hợp lệ! Vui lòng nhập /momo [Số Tiền Nạp]")
        return

    # Xử lý số tiền nạp
    amount_str = message_text[1]
    try:
        amount = int(amount_str)
    except ValueError:
        update.message.reply_text("Vui lòng nhập số tiền hợp lệ.")
        return

    if amount > 10000000:
        update.message.reply_text("Nạp đạt mức tối đa.")
        return

    if amount < 10000:
        update.message.reply_text("Nạp ít nhất 10.000 VND.")
        return

    # Thông báo chuyển khoản qua MOMO
    message = (f"<b>🧧 MOMO</b>\n\n"
               f"👉 SỐ TÀI KHOẢN : <code>0971648960</code>\n\n\n"
               f"<b>NỘI DUNG CHUYỂN</b>: <code>{user_id}</code>\n\n"
               f"<b>Lưu ý: Nạp tối thiểu 10.000đ</b>")
    update.message.reply_text(message, parse_mode='HTML')
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng lệnh /momo")

    # Thông báo cho admin
    admin_id = 5870603223
    pinned_message = context.bot.send_message(
        chat_id=admin_id,
        text=f"💵 Lệnh Nạp MOMO 💵\nUSER ID {user_id}\nSỐ TIỀN : {amount}")
    context.bot.pin_chat_message(chat_id=admin_id,
                                 message_id=pinned_message.message_id,
                                 disable_notification=False)


def bank(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_text = update.message.text.split()

    # Kiểm tra nếu người dùng bị cấm
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    # Kiểm tra đầu vào
    if len(message_text) != 2:
        update.message.reply_text(
            "Lệnh không hợp lệ! Vui lòng nhập /bank [Số Tiền Nạp]")
        return

    # Xử lý số tiền nạp
    amount_str = message_text[1]
    try:
        amount = int(amount_str)
    except ValueError:
        update.message.reply_text("Vui lòng nhập số tiền hợp lệ.")
        return

    if amount > 10000000:
        update.message.reply_text("Nạp đạt mức tối đa.")
        return

    if amount < 10000:
        update.message.reply_text("Nạp ít nhất 10.000 VND.")
        return

    # Thông báo chuyển khoản qua BANKING
    message = (f"<b>🧧 MB BANK</b>\n\n"
               f"👉 SỐ TÀI KHOẢN : <code>0971648960</code>\n\n\n"
               f"<b>NỘI DUNG CHUYỂN</b>: <code>{user_id}</code>\n\n"
               f"<b>Lưu ý: Nạp tối thiểu 10.000đ</b>")
    update.message.reply_text(message, parse_mode='HTML')
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng lệnh /bank")

    # Thông báo cho admin
    admin_id = 5870603223
    pinned_message = context.bot.send_message(
        chat_id=admin_id,
        text=f"💵 Lệnh Nạp BANKING 💵\nUSER ID {user_id}\nSỐ TIỀN : {amount}")
    context.bot.pin_chat_message(chat_id=admin_id,
                                 message_id=pinned_message.message_id,
                                 disable_notification=False)


def approve_withdraw(update: Update, context: CallbackContext):
    admin_ids = {5870603223}  # ID của các admin
    args = context.args

    if update.message.from_user.id not in admin_ids:
        update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return

    if len(args) != 3:
        update.message.reply_text(
            "❌ Sai cú pháp! Vui lòng sử dụng: /duyetrut [MOMO/BANK] [Số Tiền] [ID USER]"
        )
        return

    payment_method = args[0].upper()
    amount = args[1]
    user_id = int(args[2])

    if payment_method not in ["MOMO", "BANK"]:
        update.message.reply_text(
            "❌ Phương thức rút tiền không hợp lệ. Chỉ hỗ trợ MOMO và BANK.")
        return

    try:
        # Gửi thông báo rút tiền thành công cho user
        context.bot.send_message(
            chat_id=user_id,
            text=("<b>RÚT TIỀN THÀNH CÔNG !!!</b>\n\n"
                  f"-> Số Tiền Rút: {amount}\n"
                  f"-> Ngân Hàng Rút: {payment_method}\n\n"
                  "Cảm Ơn Bạn Đã Đồng Hành Cùng <b>[ NIGHT ROOM ]</b>"),
            parse_mode='HTML')

        # Gửi thông báo đến admin và người chơi với ID ẩn
        user_name = f"****{str(user_id)[-5:]}"  # Lấy 5 chữ số cuối của ID
        bot_3.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=(f"<b>🎉 Người chơi {user_name}</b>\n"
                  f"✅ Rút tiền thành công {format_currency(amount)}"),
            parse_mode='HTML')

        # Xác nhận với admin rằng yêu cầu rút tiền đã được xử lý
        update.message.reply_text(
            f"✅ Đã duyệt rút tiền {amount} qua {payment_method} cho ID: {user_id}"
        )

    except Exception as e:
        update.message.reply_text(f"❌ Đã xảy ra lỗi: {e}")


def decline_withdraw(update: Update, context: CallbackContext):
    admin_ids = {5870603223}  # ID của các admin
    args = context.args

    if update.message.from_user.id not in admin_ids:
        update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return

    if len(args) != 3:
        update.message.reply_text(
            "❌ Sai cú pháp! Vui lòng sử dụng: /huyrut <ID> <TIỀN> <REASON>")
        return

    user_id = int(args[0])
    amount = int(args[1])
    reason_code = args[2]

    reasons = {
        "1":
        "❌ Đơn rút của bạn đã bị hủy. Lý do: BUG BOT / BUG ROOM",
        "2":
        "❌ Đơn rút của bạn đã bị hủy. Lý do: SỬ DỤNG CODE | VUI LÒNG NẠP TIỀN MỚI ĐƯỢC SỬ DỤNG CODE RÚT",
        "3":
        ("❌ Đơn rút của bạn đã bị hủy. Lý do: Khác | Liên Hệ Admin",
         InlineKeyboardMarkup(
             [[InlineKeyboardButton("Liên Hệ Admin", url="https://t.me/.")]]))
    }

    if reason_code not in reasons:
        update.message.reply_text(
            "❌ Mã lý do không hợp lệ. Vui lòng chọn lý do từ 1, 2, hoặc 3.")
        return

    reason_message = reasons[reason_code]

    try:
        if isinstance(reason_message, tuple):
            reason_text, reply_markup = reason_message
            context.bot.send_message(chat_id=user_id,
                                     text=reason_text,
                                     reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=user_id, text=reason_message)

        user_balances[user_id] = user_balances.get(user_id, 0) + amount
        save_user_balances()

        update.message.reply_text(
            f"✅ Đã hủy đơn rút tiền {amount} cho ID: {user_id} với lý do {reason_code}"
        )

    except Exception as e:
        update.message.reply_text(f"❌ Đã xảy ra lỗi: {e}")


def duyet(update: Update, context: CallbackContext):
    global load_vip_users, vip_users, jackpot_amount
    user = update.message.from_user
    if user.id not in ADMIN_ID:
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyet <user_id> <số tiền>")
        return

    try:
        user_id_to_approve = int(context.args[0])
        amount_approved = float(context.args[1])

        # Cập nhật số dư user nạp
        if user_id_to_approve in user_balances:
            user_balances[user_id_to_approve] += amount_approved
        else:
            user_balances[user_id_to_approve] = amount_approved

        vip_users = load_vip_users()
        save_user_balances()

        if user_id_to_approve not in vip_users:
            user_balances[user_id_to_approve] = amount_approved

        # Xác định thời gian hiện tại
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")

        # Thông báo nạp thành công cho user
        user_message = (
            f"<b>✅ Nạp tiền thành công !!!!</b>\n"
            f"<b>➡️ Nội dung</b>: {user_id_to_approve}\n"
            f"<b>➡️ Thời gian</b>: {current_time}\n"
            f"<b>➡️ Số tiền:</b> {format_currency(amount_approved)}\n"
            f"<b>➡️ Số dư hiện tại:</b> {format_currency(user_balances[user_id_to_approve])}\n"
        )
        context.bot.send_message(chat_id=user_id_to_approve,
                                 text=user_message,
                                 parse_mode='HTML')

        # Thông báo cho nhóm
        masked_user_id = str(user_id_to_approve)[:-4] + "****"
        group_message = (
            f"<b>Người chơi : {masked_user_id}</b>\n"
            f"- Nạp thành công <b>{format_currency(amount_approved)}</b>")
        bot_3.send_message(chat_id=TAIXIU_GROUP_ID,
                           text=group_message,
                           parse_mode='HTML')

        # Thông báo cho admin
        admin_reply = f"Đã duyệt nạp tiền cho người dùng ID {user_id_to_approve} với số tiền {format_currency(amount_approved)} ₫."
        update.message.reply_text(admin_reply)
        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)
        context.bot.send_message(
            chat_id=ROOM_CHECK,
            text=
            (f"DUYỆT NẠP\n"
             f"ADMIN : {user.id}\n"
             f"THÊM : {format_currency(amount_approved)} CHO {user_id_to_approve}"
             ))

        # Kiểm tra và thêm user vào danh sách VIP nếu cần
        if user_id_to_approve not in vip_users:
            add_vip_user(update, context, user_id_to_approve)

        # Đọc file ref.txt để tìm sư phụ
        ref_id = None
        with open("ref.txt", "r") as ref_file:
            for line in ref_file:
                ref_entry = line.strip().split(" - ")
                if len(ref_entry) == 2 and int(
                        ref_entry[1]) == user_id_to_approve:
                    ref_id = ref_entry[0]
                    break

        if ref_id and ref_id.isdigit():
            # Tính hoa hồng ngẫu nhiên từ 5% - 10%
            commission_rate = random.uniform(0.05, 0.10)
            commission_amount = amount_approved * commission_rate

            # Cộng hoa hồng cho sư phụ
            ref_id = int(ref_id)
            user_balances[ref_id] = user_balances.get(ref_id,
                                                      0) + commission_amount
            save_user_balances()

            # Thông báo cho sư phụ
            ref_message = (
                f"Đệ tử của bạn nạp thành công. Bạn nhận được {commission_rate:.2%}% hoa hồng "
                f"từ user {user_id_to_approve}. Số tiền {format_currency(commission_amount)} đã được cộng vào tài khoản."
            )
            context.bot.send_message(chat_id=ref_id,
                                     text=ref_message,
                                     parse_mode='HTML')

        else:
            commission_rate = random.uniform(0.05, 0.10)
            commission_amount = amount_approved * commission_rate

            # Thông báo cho user nếu không có sư phụ
            no_ref_message = "Bạn không có <b>sư phụ</b>. Số tiền <b>hoa hồng</b> đã được cộng vào hũ."
            context.bot.send_message(chat_id=user_id_to_approve,
                                     text=no_ref_message,
                                     parse_mode='HTML')
            messager = f"User <b>{masked_user_id}</b> không có sư phụ. Số tiền <b>{format_currency(commission_amount)}</b> hoa hồng đã được cộng vào hũ."
            bot_3.send_message(chat_id=TAIXIU_GROUP_ID,
                               text=messager,
                               parse_mode='HTML')
            if isinstance(jackpot_amount, (int, float)):
                jackpot_amount += commission_amount

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyetnap <ID> <số tiền>")


def read_ref_file():
    if not os.path.exists(REF_FILE):
        return {}
    with open(REF_FILE, 'r') as file:
        refs = file.readlines()
    ref_dict = {}
    for ref in refs:
        inviter, invitee = ref.strip().split(' - ')
        ref_dict[int(invitee)] = int(inviter)
    return ref_dict


def write_ref_file(ref_dict):
    with open(REF_FILE, 'w') as file:
        for invitee, inviter in ref_dict.items():
            file.write(f'{inviter} - {invitee}\n')


def giftcode(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    taixiu_message = (
        f"🏆 MUA GIFTCODE\n"
        f"/muagiftCode [Số lượng giftcode] [Số tiền mỗi giftcode]\n\n"
        f"🎁 NHẬP GIFTCODE\n"
        f"/code [Tên Code]")

    context.bot.send_message(chat_id=user_id,
                             text=taixiu_message,
                             parse_mode='HTML')


def ref(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    taixiu_message = (
        f"<b>👉 Link mời bạn bè của bạn :</b>  <code>https://t.me/nightroombot?start={user_id}</code>  👈 CLICK VÀO LINK BÊN ĐỂ COPY VÀ GỬI CHO BẠN BÈ\n"
        f"🌺 Nhận ngay HOA HỒNG ngẫu nhiên từ 5% - 10% số tiền nạp từ người chơi bạn giới thiệu."
    )

    context.bot.send_message(chat_id=user_id,
                             text=taixiu_message,
                             parse_mode='HTML')


def increment_phien_number():
    phien_number = load_phien_number()
    phien_number += 1
    save_phien_number(phien_number)


def duatop(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    top_message = (
        "<b>👑 TOP CƯỢC NGÀY TRẢ THƯỞNG SÁNG HÔM SAU 👑</b>\n\n"
        "🥇 Top 1: 50.000 VND\n"
        "🥈 Top 2: 30.000 VND\n"
        "🥉 Top 3: 15.000 VND\n\n"
        "Cảm ơn các bạn đã tham gia cược! Nhấn vào nút bên dưới để nhận thưởng."
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Xem Top",
                             url="https://t.me/F88ROOMTELE_BOT?start=top")
    ]])

    context.bot.send_message(chat_id=user_id,
                             text=top_message,
                             reply_markup=keyboard,
                             parse_mode='HTML')


def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    if context.args:
        command = context.args[0].split('_')
        if command[0] == 'nap':
            nap(update, context)
    if context.args:
        command = context.args[0].split('_')
        if command[0] == 'top':
            checktop(update, context)

    if user_id not in user_balances:
        user_balances[user_id] = 2000
        save_user_balances()

        welcome_message = (
            f"👋 Xin Chào <b>{user_name}</b>, Bạn đã nhận được 2.000đ Từ Quà tặng tân thủ\n\n"
            f"<blockquote>F88: Nhà cái TOP 1️⃣ trong nền tảng TÀI XỈU Telegram.🏆</blockquote>\n\n"
            f"👤 ID Của Bạn Là <code>{user_id}</code>\n"
            f"🧧 Tham gia Room TX để săn hũ và nhận giftcode hằng ngày\n"
            f"🎗 Theo dõi Channel: Để nhận thông báo mới nhất\n")
        message_to_send = welcome_message
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
    else:
        # Nếu đã có tài khoản, chào mừng người dùng quay lại
        welcome_back_message = (
            f"👋 Xin Chào <b>{user_name}</b>, Bạn đã trở lại bot\n\n"
            f"👤 ID Của Bạn Là <code>{user_id}</code>\n"
            f"🧧 Tham gia Room TX để săn hũ và nhận giftcode hằng ngày\n"
            f"🎗 Theo dõi Channel: Để nhận thông báo mới nhất\n")
        message_to_send = welcome_back_message

    # Kiểm tra ref (link mời)
    ref_id = None
    if update.message.text.startswith('/start'):
        # Trích xuất user_id từ đường link ref (ví dụ /start?id=123456789)
        ref_id = context.args[0] if context.args else None

    if ref_id:
        if ref_id == user_id:
            context.bot.send_message(chat_id=user_id,
                                     text=f"Không thể tự mời chính mình.",
                                     parse_mode='HTML')
            return
        with open('ref.txt', 'a') as ref_file:
            ref_file.write(f"{ref_id} - {user_id}\n")

        # Gửi thông báo mời thành công
        context.bot.send_message(
            chat_id=ref_id,
            text=
            f"Mời thành công 1 người dùng {user_id}. Bạn sẽ nhận được ngẫu nhiên 5% - 10% tiền nạp sau khi người được mời nạp tiền"
        )

    # Tạo các nút bấm để người dùng lựa chọn
    buttons = [[
        InlineKeyboardButton("☄️ NIGHT ROOM",
                             url="https://t.me/nightroomtaixiu")
    ], [
        InlineKeyboardButton("🎉 KÊNH KẾT QUẢ 🎉", url="https://t.me/KQROOMF88")
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    user_keyboard = ReplyKeyboardMarkup(
        [["🎲 Room Tài Xỉu 🎲", "👤 Tài Khoản"], ["🌺 Hoa Hồng", "🎁 Giftcode"],
         ["💰 Nạp Tiền", "💸 Rút Tiền"], ["🏆 Đu Dây 🏆", "🏆 Đua Top"], ["📞 CSKH"]
         ],
        resize_keyboard=True,
        one_time_keyboard=False)

    context.bot.send_message(chat_id=user_id,
                             text=message_to_send,
                             reply_markup=keyboard,
                             parse_mode='HTML')
    context.bot.send_message(chat_id=user_id,
                             text="Chọn một tùy chọn:",
                             reply_markup=user_keyboard)
    return


@notify_usage
def game(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    taixiu_message = (
        "<b>🎲 Game Tài Xỉu Room 🎲</b>\n\n"
        "<b>Nội dung |  Tổng điểm 3 xúc xắc  |  Tỷ lệ ăn</b>\n"
        "🔴 X |  3, 4, 5, 6, 7, 8, 9, 10            |  X1.95\n"
        "🔵 T |  11, 12, 13, 14, 15, 16, 17, 18     |  X1.95\n"
        "⚪️ C |  4, 6, 8, 10, 12, 14, 16, 18        |  X1.95\n"
        "⚫️ L |  3, 5, 7, 9, 11, 13, 15, 17         |  X1.95\n"
        "<blockquote>👉 Số tiền chơi tối thiểu là 1,000đ</blockquote>\n\n"
        "Nổ Hũ : <b>XỈU 3</b> hoặc <b>TÀI 18</b>\n\n"
        "<b>🎮 Cách chơi ở ROOM :</b> Tham gia chơi ở nhóm https://t.me/F88TAIXIU\n\n"
        "<blockquote>NỘI DUNG [dấu cách] CƯỢC</blockquote>\n\n"
        "<blockquote>VD: T 10000 hoặc X 10000\nVD: T MAX hoặc X MAX</blockquote>\n\n"
        "<b>🎮 Cách chơi ẨN DANH : </b>Đơn giản cược ở bot (Tại đây) 🌈\n")

    context.bot.send_message(chat_id=user_id,
                             text=taixiu_message,
                             parse_mode='HTML')


@notify_usage
def cskh(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="📞 CSKH : [Liên hệ tại đây](https://t.me/SEMNOMEO_VN)",
        parse_mode='Markdown')
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


def handle_cskh(update: Update, context: CallbackContext):
    if update.message.text == "📞 CSKH":
        cskh(update, context)


def handle_user_buttons(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "👤 Tài Khoản":
        balance = user_balances.get(user_id, 0)
        today_bets = get_today_bets(user_id)
        account_info = (
            f"<b>👤 ID:</b> <code>{user_id}</code>\n\n"
            f"<b>💰 Số dư hiện tại:</b> {format_currency(balance)}\n\n"
            f"<b>💥 Cược hôm nay:</b> {format_currency(today_bets)}\n\n"
            f"<b>💵 Mã nạp tiền:</b> <code>{user_id}</code>")
        update.message.reply_text(account_info, parse_mode='HTML')
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")

    elif text == "💵 Tổng Cược":
        today_bets = get_today_bets(user_id)
        total_bets = (f"<b>👤 ID:</b> <code>{user_id}</code>\n"
                      f"<b>💵 Cược hôm nay:</b> {format_currency(today_bets)}")
        update.message.reply_text(total_bets, parse_mode='HTML')
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")


@notify_usage
def sd(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if user_id in user_balances:
        balance = user_balances[user_id]
        update.message.reply_text(
            f"💵 Số dư của bạn là: {format_currency(balance)} 💵")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
    else:
        update.message.reply_text("💵 Số dư của bạn là: - 💵")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")


def load_codes():
    codes = {}
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    code, value = parts
                    try:
                        codes[code] = float(value)
                    except ValueError:
                        continue
    return codes


def save_codes(codes):
    with open(CODES_FILE, 'w') as file:
        for code, value in codes.items():
            file.write(f"{code} {value}\n")


def addcode(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if update.message.from_user.id not in ADMIN_ID:
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addcode <tên code> <giá trị code>")
        return

    code_name = context.args[0]
    code_value = context.args[1]

    try:
        code_value = float(code_value)
    except ValueError:
        update.message.reply_text("Giá trị code phải là một số.")
        return

    codes = load_codes()
    codes[code_name] = code_value
    save_codes(codes)

    update.message.reply_text(
        f"Đã thêm code: {code_name} với giá trị: {format_currency(code_value)}"
    )


def message_handler(update: Update, context: CallbackContext):
    message_text = update.message.text.strip()
    if message_text == "🎲 Room Tài Xỉu 🎲":
        game(update, context)
        return
    if message_text == "💰 Nạp Tiền":
        nap(update, context)
        return
    if message_text == "💸 Rút Tiền":
        rut(update, context)
        return
    if message_text == "📊 Kết Quả Gần Nhất":
        ALO(update, context)
        return
    if message_text == "📞 CSKH":
        cskh(update, context)
        return
    if "🏆 Đu Dây Tài Xỉu 🏆" in message_text:
        chuoi(update, context)
        return
    if message_text == "🏧 Rút Bank":
        xlybank(update, context)
        return
    if message_text == "💳 Rút Momo":
        xlymomo(update, context)
        return
    if message_text == "🌺 Hoa Hồng":
        ref(update, context)
        return
    if message_text == "🎁 Giftcode":
        giftcode(update, context)
        return
    if message_text == "🏆 Đua Top":
        duatop(update, context)
        return


def redeem_code(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    vip_users = load_vip_users()

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return

    if len(context.args) != 1:
        context.bot.send_message(
            chat_id=update.message.from_user.id,
            text=
            "💵 Nhập Code \n\nNhập mã code theo định dạng:\n👉 [ /code ] dấu cách [ Mã Code ]\n\n📌 Ví dụ: /code 123456"
        )
        return

    code_name = context.args[0]
    codes = load_codes()

    if code_name not in codes:
        context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="Code không hợp lệ hoặc đã được sử dụng.")
        return

    code_value = codes.pop(code_name)

    if user_id not in vip_users:
        actual_value = code_value * 1.0
        status = "[ TÂN THỦ ]"
        thuc_nhan = "100%"
    else:
        actual_value = code_value
        status = ""
        thuc_nhan = "100%"

    if user_id not in vip_users:
        try:
            with open('tanthucode.txt', 'r') as file:
                tanthu_data = {
                    line.split()[0]: float(line.split()[1])
                    for line in file
                }
        except FileNotFoundError:
            tanthu_data = {}

        tanthu_data[str(user_id)] = tanthu_data.get(str(user_id),
                                                    0) + actual_value

        with open('tanthucode.txt', 'w') as file:
            for uid, value in tanthu_data.items():
                file.write(f"{uid} {value}\n")

    # Cập nhật số dư user
    user_balances[user_id] = user_balances.get(user_id, 0) + actual_value
    save_codes(codes)
    save_user_balances()

    # Masked user ID for group message
    masked_user_id = str(user_id)[:-4] + "****"

    # Thông báo cho user
    user_message = (
        f"💵 Bạn<b> {status}</b> đã nhận được <b>{format_currency(actual_value)}</b> từ code <b>{code_name}</b> {thuc_nhan}"
    )
    context.bot.send_message(chat_id=user_id,
                             text=user_message,
                             parse_mode='HTML')

    # Thông báo cho nhóm kiểm duyệt
    context.bot.send_message(
        chat_id=-1002424682565,
        text=(f"🛍 NHẬP CODE : {user_id} 🛍\n"
              f"Tên Code : {code_name}\n"
              f"Code có giá trị {format_currency(code_value)}."))

    # Thông báo cho nhóm Tài Xỉu
    group_message = (
        f"💵 User <b>{masked_user_id} {status}</b>\n"
        f"Nhập Thành Công Giftcode <b>{code_name}</b>\n\n💎 Giá Trị <b>{format_currency(code_value)}</b>\n"
        f"Thực Nhận : +<b>{format_currency(actual_value)}</b>")
    bot_5.send_message(chat_id=TAIXIU_GROUP_ID,
                       text=group_message,
                       parse_mode='HTML')


def clearall(update: Update, context: CallbackContext):
    if update.message.from_user.id != 5870603223:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    open("onecode.txt", "w").close()
    open("usedcode.txt", "w").close()

    update.message.reply_text("Đã xóa tất cả mã code và mã đã sử dụng.")


@notify_usage
def addsodu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if update.message.from_user.id not in ADMIN_ID:
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addsd <user_id> <số tiền>")
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])

        if user_id in user_balances:
            user_balances[user_id] += amount
        else:
            user_balances[user_id] = amount

        save_user_balances()
        update.message.reply_text(
            f"Đã cộng {format_currency(amount)} vào tài khoản {user_id}. Số dư hiện tại: {format_currency(user_balances[user_id])}"
        )
        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)
        context.bot.send_message(chat_id=-1002424682565,
                                 text=(f"🔰 ADMIN ADD SỐ DƯ 🔰\n"
                                       f"ADMIN ID : {user_id}\n"
                                       f"Cộng {format_currency(amount)}"))

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addsd <user_id> <số tiền>")


def generate_gift_codes(quantity, price_per_code):
    codes = {}
    for _ in range(quantity):
        code = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=8))
        codes[code] = price_per_code
    return codes


def generate_gift_code(min_value, max_value):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    value = random.randint(min_value, max_value)
    return code, value


def load_message_count():
    if os.path.exists(MESSAGE_COUNT_FILE):
        with open(MESSAGE_COUNT_FILE, 'r') as file:
            try:
                data = json.load(file)
                if isinstance(data, dict) and "count" in data:
                    return data["count"]
                else:
                    save_message_count(0)
                    return 0
            except json.JSONDecodeError:
                save_message_count(0)
                return 0
    else:
        save_message_count(0)
        return 0


def save_message_count(count):
    with open(MESSAGE_COUNT_FILE, 'w') as file:
        json.dump({"count": count}, file)


def send_gift_code_to_user(user_id, code, value, context):
    try:
        context.bot.send_message(chat_id=user_id,
                                 text=f"🎁 Đây là mã giftcode của bạn: {code}\n"
                                 f"💰 Giá trị: {value} VND\n"
                                 f"Hãy nhập mã này vào hệ thống để sử dụng.")
    except Exception as e:
        print(f"Error sending gift code to user {user_id}: {str(e)}")


@notify_usage
def muagiftcode(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    vip_user = load_vip_users()

    if user_id not in vip_user:
        update.message.reply_text("Tân thủ không thể đổi code.")
        return

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return
    if not update.message:
        return

    user_name = update.message.from_user.first_name

    try:
        member = context.bot.get_chat_member(chat_id=update.message.chat_id,
                                             user_id=user_id)
        if member.status in [ChatMember.LEFT, ChatMember.KICKED]:
            return
    except:
        update.message.reply_text(
            "Có lỗi xảy ra khi kiểm tra trạng thái thành viên.")
        return

    message_text = update.message.text.strip().split()

    if len(message_text) != 3:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            "Vui lòng nhập theo định dạng: /muagiftCode [số lượng giftcode] [số tiền mỗi giftcode]"
        )
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    try:
        quantity = int(message_text[1])
        price_per_code = int(message_text[2])
    except ValueError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Số lượng giftcode và số tiền mỗi giftcode phải là số nguyên."
        )
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    if quantity < 5 or quantity > 50:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Số lượng giftcode phải từ 5 đến 10.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    if price_per_code < 5000:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Số tiền mỗi giftcode phải lớn hơn 5,000 VND.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    total_cost = quantity * price_per_code
    fee = total_cost * 0.1
    final_cost = total_cost + fee

    if user_balances.get(user_id, 0) < final_cost:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            f"Số dư của bạn không đủ để mua {quantity} giftcode với giá {price_per_code} mỗi giftcode."
        )
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    codes = generate_gift_codes(quantity, price_per_code)

    existing_codes = load_codes()
    existing_codes.update(codes)
    save_codes(existing_codes)

    user_balances[user_id] -= final_cost

    codes_message = "\n".join(
        [f"👉 <code>{code}</code>" for code, value in codes.items()])

    context.bot.send_message(chat_id=-1002424682565,
                             text=(f"💝 MUA GIFTCODE 💝\n"
                                   f"ID: {user_id}\n"
                                   f"Giftcodes:\n{codes_message}\n"
                                   f"Code có giá trị {price_per_code}."),
                             parse_mode=ParseMode.HTML)

    context.bot.send_message(
        chat_id=user_id,
        text=(f"🛍 Đã mua thành công {quantity} giftcode\n\n"
              f"Ấn vào để copy:\n{codes_message}"),
        parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")
    bot_5.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text=(f"<b>Vừa có user mua thành công {quantity} Giftcode 🎁</b>"),
        parse_mode="html")


@notify_usage
def delsodu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        return
    if update.message.from_user.id != 5870603223:
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /delsd <user_id> <số tiền>")
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])

        if user_id in user_balances:
            user_balances[user_id] -= amount
        else:
            user_balances[user_id] = amount

        save_user_balances()
        update.message.reply_text(
            f"Đã trừ {format_currency(amount)} vào tài khoản {user_id}. Số dư hiện tại: {format_currency(user_balances[user_id])}"
        )
        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /delsd <user_id> <số tiền>")


@notify_usage
def napthe(update, context):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    user_id = update.message.from_user.id

    if len(context.args) != 4:
        update.message.reply_text(
            "💳 NẠP THẺ 💳\n\nLệnh Nạp /napthe <Seri> <Card> <Nhà Mạng> <Mệnh Giá>\n\nTự động duyệt nạp thẻ trong 10s"
        )
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    seri, card, nha_mang, menh_gia = context.args

    if nha_mang.lower() not in [
            'viettel', 'vinaphone', 'mobiphone', 'vietnamobile'
    ]:
        update.message.reply_text(
            "Nhà mạng không hợp lệ. Vui lòng chọn trong [Viettel, Vinaphone, Mobiphone, Vietnamobile]."
        )
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    if menh_gia not in MENH_GIA:
        update.message.reply_text("Mệnh giá không hợp lệ.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return

    admin_message = (
        f"<b>Yêu cầu nạp thẻ mới:</b>\n"
        f"<b>Người dùng:</b> {update.message.from_user.full_name}\n"
        f"<b>Seri:</b> <code>{seri}</code>\n"
        f"<b>Card:</b> <code>{card}</code>\n"
        f"<b>Nhà mạng:</b> {nha_mang}\n"
        f"<b>Mệnh giá:</b> {menh_gia}\n\n"
        f"<i>User ID</i> : <code>{user_id}</code> ")

    context.bot.send_message(chat_id=5870603223,
                             text=admin_message,
                             parse_mode='HTML')
    update.message.reply_text(
        "Yêu cầu của bạn đã được gửi. Vui lòng đợi phản hồi.")
    update.message.reply_text("Mệnh giá đang được xử lý ...")
    update.message.reply_text(
        "Error 404. Check Connection API Hosting | Liên hệ admin")
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


@notify_usage
def duyetnapthe(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        return
    admin_id = 5870603223
    if update.message.from_user.id != admin_id:
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng cung cấp đầy đủ thông tin: /duyetnapthe <id user> <số tiền>"
        )
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyetnapthe <id user> <số tiền>")
        return

    fee = amount * 0.2
    final_amount = amount - fee

    if user_id in user_balances:
        user_balances[user_id] += final_amount
    else:
        user_balances[user_id] = final_amount

    save_user_balances()
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
    group_messages = (f"✅ Nạp thẻ thành công !!!!\n"
                      f"➡️ Số tiền: {format_currency(final_amount)}\n"
                      f"➡️ Thời gian: {current_time}")
    bot_3.send_message(chat_id=user_id, text=group_messages)

    masked_user_id = user_id[:-4] + "****"
    group_message = (f"Người chơi ID: {masked_user_id}\n"
                     f"- Nạp thành công {amount} đ")

    context.bot.send_message(chat_id=TAIXIU_GROUP_ID, text=group_message)


@notify_usage
def profile(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return
    user = update.message.from_user
    user_id = user.id
    user_full_name = user.full_name
    username = user.username or "N/A"
    balance = user_balances.get(user_id, 0)

    vip_users = load_vip_users()

    if user_id == 5870603223:
        status = "🔰 ADMIN 🔰"
    elif user_id in vip_users:
        status = "✅ Người Chơi ✅"
    else:
        status = "❌ Tân thủ ❌"

    profile_message = (f"┌─┤Thông tin người dùng├──⭓\n"
                       f"├Tên : {user_full_name}\n"
                       f"├UID : {user_id}\n"
                       f"├Username : @{username}\n"
                       f"├Số Dư : {balance} VND 💵\n"
                       f"├Trạng thái : {status}\n"
                       f"└───────────────⭓")

    keyboard = [[
        InlineKeyboardButton("💸 Nạp tiền 💸",
                             url='https://t.me/botTX1_bot?start=nap')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(profile_message, reply_markup=reply_markup)
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


@notify_usage
def chat(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if update.message.from_user.id not in ADMIN_ID:
        return
    if len(context.args) < 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /chat <ID user> <nội dung>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        update.message.reply_text("ID user phải là một số nguyên.")
        return

    message_text = ' '.join(context.args[1:])

    try:
        context.bot.send_message(chat_id=user_id, text=message_text)
        update.message.reply_text("Thông báo đã được gửi.")
    except Exception as e:
        update.message.reply_text(f"Không thể gửi thông báo: {e}")


@notify_usage
def check_user_profile(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        return
    if update.message.from_user.id not in ADMIN_ID:
        return
    if not context.args:
        update.message.reply_text(
            "Vui lòng nhập ID người dùng để kiểm tra thông tin.")
        return

    try:
        user_id_to_check = int(context.args[0])
    except ValueError:
        update.message.reply_text("ID người dùng không hợp lệ.")
        return

    user = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                       user_id=user_id_to_check).user
    user_id = user.id
    user_full_name = user.full_name
    username = user.username or "N/A"
    balance = user_balances.get(user_id, 0)

    vip_users = load_vip_users()

    if user_id == 5870603223:
        status = "🔰 ADMIN 🔰"
    elif user_id in vip_users:
        status = "✅ Người Chơi ✅"
    else:
        status = "❌ Tân thủ ❌"

    profile_message = (f"┌─┤Thông tin người dùng├──⭓\n"
                       f"├Tên : {user_full_name}\n"
                       f"├UID : {user_id}\n"
                       f"├Username : @{username}\n"
                       f"├Số Dư : {balance} VND 💵\n"
                       f"├Trạng thái : {status}\n"
                       f"└───────────────⭓")

    update.message.reply_text(profile_message)


@notify_usage
def set_jackpot(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        return
    if user_id not in ADMIN_ID:
        return

    if len(context.args) != 1:
        jackpot_amount = 50000
        with open('jackpot.txt', 'w') as f:
            f.write(str(jackpot_amount))
        update.message.reply_text(
            f"Jackpot amount set to default value: {jackpot_amount}")
        return

    try:
        new_amount = int(context.args[0])
        with open('jackpot.txt', 'w') as f:
            f.write(str(new_amount))
        update.message.reply_text(
            f"Jackpot amount set to: {format_currency(new_amount)}")
    except ValueError:
        update.message.reply_text(
            "Invalid amount. Please provide a valid integer.")


def clear_old_entries():
    now = datetime.now()
    for user_id in list(user_command_times):
        user_command_times[user_id] = [
            time for time in user_command_times[user_id]
            if now - time < timedelta(seconds=120)
        ]
        if not user_command_times[user_id]:
            del user_command_times[user_id]


def generate_new_code():
    code_length = 6
    letters_and_digits = string.ascii_letters + string.digits
    new_code = ''.join(
        random.choice(letters_and_digits) for i in range(code_length))
    return new_code


def reset_usage_count(user_id):
    global usage_count, last_reset_time
    usage_count[user_id] = 0
    last_reset_time[user_id] = time.time()


def log_group_command(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id
    chat_title = update.message.chat.title
    command = update.message.text

    full_name = user.full_name if user.full_name else "N/A"
    username = user.username if user.username else "N/A"
    user_id = user.id

    print(f"{Fore.CYAN}┌─┤{Fore.RED}PHÁT HIỆN{Fore.CYAN}├──⭓")
    print(f"{Fore.CYAN}├{Fore.GREEN} Tên : {Fore.BLUE}{full_name}")
    print(f"{Fore.CYAN}├{Fore.GREEN} UID : {Fore.BLUE}{user_id}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Username : {Fore.BLUE}@{username}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Box : {Fore.BLUE}{chat_title}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Chat ID : {Fore.BLUE}{chat_id}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Nội dung : {Fore.BLUE}{command}")
    print(f"{Fore.CYAN}└───────────────⭓")


@notify_usage
def ban_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        return

    if len(context.args) == 0:
        update.message.reply_text("Bạn cần cung cấp ID để ban người dùng.")
        return

    user_id = context.args[0]

    with open("banuser.txt", "a") as file:
        file.write(str(user_id) + "\n")

    update.message.reply_text(
        f"Đã ban người dùng có ID {user_id} khỏi sử dụng bot.")


def is_user_banned(user_id):
    banned_users = set()
    with open("banuser.txt", "r") as file:
        for line in file:
            banned_users.add(line.strip())
    return str(user_id) in banned_users


def update_code_every_5_minutes(bot: Bot):
    while True:
        time.sleep(300)

        code = generate_new_code()
        code_value = random.randint(100, 10000)

        with open(CODES_FILE, 'a') as file:
            file.write(f"{code} {code_value}\n")

        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vn_tz)
        seconds = random.randint(3000, 12000)
        next_code_time = current_time + timedelta(seconds)
        next_code_time_str = next_code_time.strftime("%H:%M:%S")

        keyboard_1 = [[
            InlineKeyboardButton("🎁 Nhập Code 🎁",
                                 url="https://t.me/F88TAIXIUTELE")
        ]]
        reply_markup_1 = InlineKeyboardMarkup(keyboard_1)

        bot.send_message(
            chat_id=ROOM_KQ,
            text=(f"<b>🎲 Phát code ngẫu nhiên trong ngày 🎲</b>\n\n"
                  f"😍😍 <b>Code là</b> : <code>{code}</code> 😍😍\n\n"
                  f"⭕️ <b>Cách nhận</b> : /code [Code]\n\n"
                  f"⛔️ <b>Lưu Ý</b> : Code chỉ sài được 1 lần\n"),
            reply_markup=reply_markup_1,
            parse_mode='HTML')

        keyboard_2 = [[
            InlineKeyboardButton("🍀 Room Kết Quả ",
                                 url="https://t.me/KQROOMF88")
        ]]
        reply_markup_2 = InlineKeyboardMarkup(keyboard_2)

        bot_5.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=(
                "<b>[ GIFTCODE ]</b> Room KQ Vừa Phát Code <b>Ngẫu Nhiên</b> ☘️"
            ),
            reply_markup=reply_markup_2,
            parse_mode='html')


def freecode(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    code = generate_new_code()
    code_value = random.randint(100, 5000)

    if user_id != 5870603223:
        return

    with open(CODES_FILE, 'a') as file:
        file.write(f"{code} {code_value}\n")

    keyboard_1 = [[
        InlineKeyboardButton("🎁 Nhập Code 🎁", url="https://t.me/F88TAIXIUTELE")
    ]]
    reply_markup_1 = InlineKeyboardMarkup(keyboard_1)

    bot_5.send_message(chat_id=ROOM_KQ,
                       text=(f"<b>🎲 Phát code ngẫu nhiên trong ngày 🎲</b>\n\n"
                             f"😍😍 <b>Code là</b> : <code>{code}</code> 😍😍\n\n"
                             f"⭕️ <b>Cách nhận</b> : /code [Code]\n\n"
                             f"⛔️ <b>Lưu Ý</b> : Code chỉ sài được 1 lần\n"),
                       reply_markup=reply_markup_1,
                       parse_mode='HTML')

    keyboard_2 = [[
        InlineKeyboardButton("🍀 Room Kết Quả ",
                             url="https://t.me/F88TAIXIUTELE")
    ]]
    reply_markup_2 = InlineKeyboardMarkup(keyboard_2)

    bot_5.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text=(
            "<b>[ GIFTCODE ]</b> Room KQ Vừa Phát Code <b>Ngẫu Nhiên</b> ☘️"),
        reply_markup=reply_markup_2,
        parse_mode='html')


@notify_usage
def ALO(update: Update, context: CallbackContext):
    global recent_results
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return
    update.message.reply_text(
        f"🗒 Kết quả 10 phiên gần nhất:\n{format_recent_results()}")
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


@notify_usage
def menu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        context.bot.send_message(chat_id=ROOM_CHECK1,
                                 text=f"User {user_id} sử dụng 1 lệnh của bot")
        return
    keyboard = [["T 1000", "T 5000", "X 1000", "X 5000"],
                ["T 10000", "T 50000", "X 10000", "X 50000"],
                ["👤 Tài Khoản", "💵 Tổng Cược"],
                ["🏆 Đu Dây Tài Xỉu 🏆", "📊 Kết Quả Gần Nhất"]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text("Menu Bot", reply_markup=reply_markup)
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


@notify_usage
def delbet(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        amount_to_deduct = int(context.args[1])

        bets = {}
        if os.path.exists("tongcuoc.txt"):
            with open("tongcuoc.txt", "r") as file:
                for line in file:
                    line_user_id, line_bet_amount = line.strip().split()
                    bets[line_user_id] = int(float(line_bet_amount))

        if user_id in bets:
            bets[user_id] -= amount_to_deduct
            if bets[user_id] < 0:
                bets[user_id] = 0

            with open("tongcuoc.txt", "w") as file:
                for line_user_id, line_bet_amount in bets.items():
                    file.write(f"{line_user_id} {line_bet_amount}\n")

            update.message.reply_text(
                f"Đã trừ {amount_to_deduct} từ ID {user_id}. Số dư hiện tại: {bets[user_id]}"
            )
        else:
            update.message.reply_text(
                f"Không tìm thấy ID {user_id} trong danh sách cược.")

    except (IndexError, ValueError):
        update.message.reply_text("Sử dụng lệnh: /delbet <ID> <Số tiền trừ>")


@notify_usage
def checkbet(update: Update, context: CallbackContext):
    try:
        user_id = context.args[0]

        bets = {}
        if os.path.exists("tongcuoc.txt"):
            with open("tongcuoc.txt", "r") as file:
                for line in file:
                    line_user_id, line_bet_amount = line.strip().split()
                    bets[line_user_id] = int(float(line_bet_amount))

        if user_id in bets:
            update.message.reply_text(
                f"Số tiền cược của ID {user_id} là: {bets[user_id]}")
        else:
            update.message.reply_text(
                f"Không tìm thấy ID {user_id} trong danh sách cược.")

    except (IndexError, ValueError):
        update.message.reply_text("Sử dụng lệnh: /checkbet <ID>")


@notify_usage
def checktop(update: Update, context: CallbackContext):
    bets = {}

    if os.path.exists("tongcuoc.txt"):
        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                if line_user_id not in ADMIN_ID:
                    bets[line_user_id] = int(float(line_bet_amount))

    # Chỉ lấy top 3
    top_bets = sorted(bets.items(), key=lambda item: item[1], reverse=True)[:3]

    top_message = "<b>👑 TOP CƯỢC NGÀY HÔM NAY 👑</b>\n\n"

    # Định dạng cho 3 top đầu
    for i, (user_id, bet_amount) in enumerate(top_bets):
        rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        top_message += f"{rank_emoji} <b>TOP {i + 1}:</b> <code>{user_id}</code> - Tổng Cược: {format_currency(bet_amount)}\n"

    # Gửi tin nhắn tới người dùng và thông báo sử dụng bot
    update.message.reply_text(top_message, parse_mode=ParseMode.HTML)
    context.bot.send_message(
        chat_id=ROOM_CHECK1,
        text=f"User {update.message.from_user.id} sử dụng 1 lệnh của bot")


@notify_usage
def resetbet(update: Update, context: CallbackContext):
    if update.message.from_user.id != 5870603223:
        return

    with open("tongcuoc.txt", "w") as file:
        file.write("")

    update.message.reply_text("File tongcuoc.txt đã được đặt lại thành rỗng.")


@notify_usage
def tatmenu(update: Update, context: CallbackContext):
    keyboard = ReplyKeyboardRemove()

    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Menu đã được tắt.",
                             reply_markup=keyboard)


@notify_usage
def chuoi(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    user_id = update.message.from_user.id
    winning_streak = winning_streaks.get(user_id, 0)
    losing_streak = losing_streaks.get(user_id, 0)

    streak_message = (f"<b>🏆 Chuỗi Thắng:</b> {winning_streak}\n"
                      f"<b>🏆 Chuỗi Thua:</b> {losing_streak}")

    update.message.reply_text(streak_message, parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=ROOM_CHECK1,
                             text=f"User {user_id} sử dụng 1 lệnh của bot")


def load_user_bet_amounts():
    user_bet_amounts = {}
    try:
        with open('tongcuoc.txt', 'r') as file:
            for line in file:
                user_id, bet_amount = line.strip().split()
                user_bet_amounts[float(user_id)] = float(bet_amount)
    except FileNotFoundError:
        pass
    return user_bet_amounts


def reset_bets(update, context):
    with open("tongcuoc.txt", "w") as file:
        file.write("")
    update.message.reply_text("Đã reset cược tất cả người dùng.")


def send_daily_top_rewards(update: Update, context: CallbackContext):
    if os.path.exists("tongcuoc.txt"):
        bets = {}

        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                bets[line_user_id] = int(float(line_bet_amount))

        top_bets = sorted(bets.items(), key=lambda item: item[1],
                          reverse=True)[:3]
        current_date = datetime.now(VN_TZ).strftime("%d/%m")

        top_message = (
            f"🔥 <b>Top cược ngày hôm qua {current_date}!</b> 🔥\n\n"
            f"🥇 Top 1: ****{str(top_bets[0][0])[-5:]}  |  {format_currency(top_bets[0][1])} VND\n"
            f"🥈 Top 2: ****{str(top_bets[1][0])[-5:]}  |  {format_currency(top_bets[1][1])} VND\n"
            f"🥉 Top 3: ****{str(top_bets[2][0])[-5:]}  |  {format_currency(top_bets[2][1])} VND\n\n"
            "NIGHT ROOM ĐÃ TRẢ THƯỞNG 🔥")

        # Gửi tin nhắn vào nhóm và lấy message_id để ghim
        message = context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                           text=top_message,
                                           parse_mode='HTML')

        # Ghim tin nhắn trả thưởng
        context.bot.pin_chat_message(
            chat_id=TAIXIU_GROUP_ID,
            message_id=message.message_id,
            disable_notification=True  # Ghim không thông báo
        )

        # Cộng thưởng cho top 3 user và lưu lại số dư mới
        reward_amounts = [50000, 30000, 15000]
        for i, (user_id, _) in enumerate(top_bets):
            user_balances[user_id] = user_balances.get(user_id,
                                                       0) + reward_amounts[i]

        save_user_balances()

        # Xóa nội dung file "tongcuoc.txt" sau khi trả thưởng
        with open("tongcuoc.txt", "w") as file:
            file.write("")


def main():
    # Tải kết quả từ các file khi chương trình bắt đầu
    load_taixiu_results()
    load_chanle_results()
    load_recent_results()
    load_user_balances()
    read_balances()
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    bot = Bot(TOKEN)
    context = CallbackContext(dispatcher)
    start_taixiu(None, context)

    dispatcher.add_handler(CommandHandler("donetop", send_daily_top_rewards))

    dispatcher.add_handler(CommandHandler("rb", reset_bets))

    dispatcher.add_handler(CommandHandler("tatmenu", tatmenu))
    dispatcher.add_handler(CommandHandler("top", checktop))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addsd", addsodu))
    dispatcher.add_handler(CommandHandler("delsd", delsodu))
    dispatcher.add_handler(CommandHandler("menu", menu))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)t\s+(max|\d+)$'), taixiu_bet))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)x\s+(max|\d+)$'), taixiu_bet))
    # Thêm MessageHandler cho cược
    # Xử lý các lệnh bắt đầu bằng 'C' theo sau là 'max' hoặc số
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)c\s+(max|\d+)$'), taixiu_bet))

    # Xử lý các lệnh bắt đầu bằng 'L' theo sau là 'max' hoặc số
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)l\s+(max|\d+)$'), taixiu_bet))
    dispatcher.add_handler(CommandHandler("nap", nap))
    dispatcher.add_handler(CommandHandler("momo", momo))
    dispatcher.add_handler(CommandHandler("huyrut", decline_withdraw))
    dispatcher.add_handler(CommandHandler("bank", bank))
    dispatcher.add_handler(CommandHandler("sd", sd))
    dispatcher.add_handler(CommandHandler("addcode", addcode))
    dispatcher.add_handler(CommandHandler("code", redeem_code))
    dispatcher.add_handler(CommandHandler("duyetnap", duyet))
    dispatcher.add_handler(CommandHandler("muagiftcode", muagiftcode))
    dispatcher.add_handler(CommandHandler("napthe", napthe))
    dispatcher.add_handler(CommandHandler("profile", profile))
    dispatcher.add_handler(CommandHandler("chat", chat))
    dispatcher.add_handler(CommandHandler('checkid', check_user_profile))
    dispatcher.add_handler(CommandHandler("set", set_jackpot))
    dispatcher.add_handler(CommandHandler("napthe", napthe))
    dispatcher.add_handler(CommandHandler("duyetnapthe", duyetnapthe))
    dispatcher.add_handler(CommandHandler("cau", ALO))
    dispatcher.add_handler(CommandHandler("chuoi", chuoi))
    dispatcher.add_handler(CommandHandler("notiall", notiall))
    dispatcher.add_handler(CommandHandler("rut", rut))
    dispatcher.add_handler(CommandHandler("duyetrut", approve_withdraw))
    dispatcher.add_handler(CommandHandler("rutbank", rutbank))
    dispatcher.add_handler(CommandHandler("freecodeadminright", freecode))
    dispatcher.add_handler(CommandHandler("rutmomo", rutmomo))

    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)👤\s+Tài\s+Khoản$'),
                       handle_user_buttons))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)💵\s+Tổng\s+Cược$'),
                       handle_user_buttons))
    dispatcher.add_handler(CallbackQueryHandler(nap, pattern='nap'))
    dispatcher.add_handler(
        MessageHandler(Filters.text & (~Filters.command), message_handler))
    dispatcher.add_handler(
        MessageHandler(Filters.group & (~Filters.command), log_group_command))
    ban_handler = CommandHandler('banuser', ban_user)
    threading.Thread(target=update_code_every_5_minutes,
                     args=(bot, ),
                     daemon=True).start()
    dispatcher.add_handler(ban_handler)
    dispatcher.add_handler(CommandHandler("cskh", cskh))
    global winning_streaks, losing_streaks
    winning_streaks = load_streaks("chuoithang.txt")
    losing_streaks = load_streaks("chuoithua.txt")

    import traceback

    # Đặt múi giờ Việt Nam
    vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

    # Hàm xử lý lỗi
    def error_handler(update, context):
        try:
            raise context.error
        except Exception as e:
            # Thời gian lỗi với múi giờ Việt Nam
            error_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")

            # Stack trace để xác định lỗi xảy ra ở đâu
            error_traceback = traceback.format_exc()

            # Ghi lỗi ra console
            print(f"[{error_time}] Lỗi nghiêm trọng: {e}")
            print(f"Chi tiết lỗi:\n{error_traceback}")

            # Ghi lỗi vào file error.txt
            with open("error.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"[{error_time}] Lỗi nghiêm trọng: {str(e)}\n")
                log_file.write(f"Chi tiết lỗi:\n{error_traceback}\n")

    # Đăng ký error_handler với dispatcher
    dispatcher.add_error_handler(error_handler)

    # Bắt đầu chạy bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
