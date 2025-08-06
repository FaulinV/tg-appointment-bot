# Telegram Booking Bot
# Repository: https://github.com/FaulinV
# Developed by Zhan Kornilov (Faulin)

import warnings
warnings.filterwarnings("ignore", ".*per_message.*", category=UserWarning)

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import datetime
import re

# --- CONFIGURATION ---
# TOKEN placeholder - replace with your bot token
TOKEN = 'PASTE_YOUR_API_TOKEN_HERE'
# ADMIN_CHAT_ID placeholder - replace with your admin chat ID
ADMIN_CHAT_ID = 'PASTE_YOUR_ADMIN_CHAT_ID_HERE'

# --- STATES ---
ASK_NAME, ASK_PHONE = range(2)

# --- STORAGE ---
# user_lang maps user IDs to language codes ('en' or 'ru')
user_lang = {}
# bookings stores date -> time -> booking info
bookings = {}
# to_notify stores user-specific list of bookings
to_notify = {}

# --- TRANSLATIONS ---
TRANSLATIONS = {
    'button_record':     {'en':'Book Repair 🛠️',       'ru':'Записать на ремонт 🛠️'},
    'button_my_bookings':{'en':'My Appointments 📋',   'ru':'Мои записи 📋'},
    'button_clients':    {'en':'Clients 👥',           'ru':'Клиенты 👥'},
    'button_language':   {'en':'Language 🌐',          'ru':'Язык 🌐'},
    'prompt_welcome':    {
        'en':'Hello, {name}! Welcome to Computer Repair Service.',
        'ru':'Привет, {name}! Добро пожаловать в сервис ремонта компьютеров.'
    },
    'prompt_choose_day': {
        'en':'Select a day for your repair appointment:',
        'ru':'Выберите день для ремонта:'
    },
    'prompt_choose_time':{
        'en':'Select a time on {date}:',
        'ru':'Выберите время на {date}:'
    },
    'prompt_ask_name':   {
        'en':'Please enter your full name:',
        'ru':'Пожалуйста, введите ваше полное имя:'
    },
    'prompt_ask_phone':  {
        'en':'Press the button below to share your phone number:',
        'ru':'Нажмите кнопку ниже, чтобы отправить номер телефона:'
    },
    'error_phone_format':{
        'en':'Only numbers allowed, you can include a leading +',
        'ru':'Только цифры и необязательный + в начале'
    },
    'error_phone_length':{
        'en':'Maximum 12 digits allowed!',
        'ru':'Максимум 12 цифр!'
    },
    'user_sent':         {
        'en':'Your repair request for {date} at {time} has been sent. Please wait for confirmation.',
        'ru':'Ваша заявка на ремонт {date} в {time} отправлена. Ожидайте подтверждения.'
    },
    'no_bookings':       {
        'en':'You have no scheduled appointments.',
        'ru':'У вас нет запланированных записей.'
    },
    'your_bookings':     {
        'en':'Your Appointments:',
        'ru':'Ваши записи:'
    },
    'all_clients':       {
        'en':'All confirmed clients:',
        'ru':'Все подтверждённые клиенты:'
    },
    'prompt_language':   {
        'en':'Choose language:',
        'ru':'Выберите язык:'
    },
    'lang_set':          {
        'en':'Language set to English.',
        'ru':'Язык установлен на русский.'
    }
}

# Days of week for selection
DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday']
# Time slots for bookings
TIMES = [f"{h:02d}:00" for h in range(9, 18)]

# --- HELPERS ---

def fmt_date(dt: datetime.date) -> str:
    return dt.strftime('%Y-%m-%d')

def next_weekday(idx: int) -> datetime.date:
    today = datetime.date.today()
    delta = (idx - today.weekday() + 7) % 7 or 7
    return today + datetime.timedelta(days=delta)

# Language helper

def get_user_lang(uid):
    return user_lang.get(uid, 'en')

def trans(key, uid, **kwargs):
    template = TRANSLATIONS[key][get_user_lang(uid)]
    return template.format(**kwargs)

# Main keyboard builder
def main_kb(uid):
    row1 = [trans('button_record', uid)]
    if str(uid) == str(ADMIN_CHAT_ID):
        row2 = [trans('button_clients', uid), trans('button_language', uid)]
    else:
        row2 = [trans('button_my_bookings', uid), trans('button_language', uid)]
    return ReplyKeyboardMarkup([row1, row2], resize_keyboard=True)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or ''
    await update.message.reply_text(
        trans('prompt_welcome', uid, name=name),
        reply_markup=main_kb(uid)
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Your user ID: {uid}")

async def menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    if text == trans('button_language', uid):
        kb = [
            [InlineKeyboardButton('🇬🇧 English', callback_data='lang|en')],
            [InlineKeyboardButton('🇷🇺 Русский', callback_data='lang|ru')]
        ]
        await update.message.reply_text(trans('prompt_language', uid), reply_markup=InlineKeyboardMarkup(kb))
        return
    if text == trans('button_record', uid):
        kb = [[InlineKeyboardButton(DAYS[i], callback_data=f'day|{i}')] for i in range(len(DAYS))]
        await update.message.reply_text(trans('prompt_choose_day', uid), reply_markup=InlineKeyboardMarkup(kb))
        return
    if text == trans('button_my_bookings', uid) and str(uid) != str(ADMIN_CHAT_ID):
        recs = to_notify.get(uid, [])
        if not recs:
            await update.message.reply_text(trans('no_bookings', uid), reply_markup=main_kb(uid))
            return
        msg = trans('your_bookings', uid) + "\n"
        for r in recs:
            msg += f"{r['date']} at {r['time']} - Status: {r['status']}\n"
        await update.message.reply_text(msg, reply_markup=main_kb(uid))
        return
    if text == trans('button_clients', uid) and str(uid) == str(ADMIN_CHAT_ID):
        msg = trans('all_clients', uid) + "\n"
        for client_id, recs in to_notify.items():
            for r in recs:
                if r['status'] == 'confirmed':
                    msg += f"{r['date']} at {r['time']} - {r['client_name']} ({r['phone']})\n"
        await update.message.reply_text(msg, reply_markup=main_kb(uid))
        return

async def callback_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    _, code = query.data.split('|')
    user_lang[uid] = code
    await query.edit_message_text(trans('lang_set', uid))
    name = query.from_user.first_name or ''
    await context.bot.send_message(uid, trans('prompt_welcome', uid, name=name), reply_markup=main_kb(uid))

async def callback_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    idx = int(query.data.split('|')[1])
    ds = fmt_date(next_weekday(idx))
    context.user_data['date'] = ds
    booked = bookings.get(ds, {})
    kb = []
    for t in TIMES:
        label = f"{t} (booked)" if t in booked else t
        cb = 'ignore' if t in booked else f'time|{t}'
        kb.append([InlineKeyboardButton(label, callback_data=cb)])
    kb.append([InlineKeyboardButton('Back', callback_data='back_day')])
    await query.edit_message_text(trans('prompt_choose_time', uid, date=ds), reply_markup=InlineKeyboardMarkup(kb))

async def callback_back_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    kb = [[InlineKeyboardButton(DAYS[i], callback_data=f'day|{i}')] for i in range(len(DAYS))]
    await query.edit_message_text(trans('prompt_choose_day', uid), reply_markup=InlineKeyboardMarkup(kb))

async def time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    context.user_data['time'] = query.data.split('|')[1]
    await query.edit_message_text(trans('prompt_ask_name', uid))
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    context.user_data['client_name'] = update.message.text
    kb = ReplyKeyboardMarkup([[KeyboardButton('Share Contact', request_contact=True)]], resize_keyboard=True)
    await update.message.reply_text(trans('prompt_ask_phone', uid), reply_markup=kb)
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    uid = update.effective_user.id
    if not contact:
        if not re.fullmatch(r"\+?\d+", phone):
            await update.message.reply_text(trans('error_phone_format', uid))
            return ASK_PHONE
        digits = re.sub(r"\D", "", phone)
        if len(digits) > 12:
            await update.message.reply_text(trans('error_phone_length', uid))
            return ASK_PHONE
    ds = context.user_data['date']
    ts = context.user_data['time']
    name_client = context.user_data['client_name']
    bookings.setdefault(ds, {})[ts] = {'client_id':uid,'client_name':name_client,'phone':phone,'status':'pending'}
    to_notify.setdefault(uid, []).append({'date':ds,'time':ts,'client_name':name_client,'phone':phone,'status':'pending'})
    admin_msg = f"New repair booking:\nClient: {name_client}\nPhone: {phone}\nDate: {ds}\nTime: {ts}" 
    buttons = [[InlineKeyboardButton('Confirm', callback_data=f'confirm|{uid}|{ds}|{ts}')],
               [InlineKeyboardButton('Deny', callback_data=f'deny|{uid}|{ds}|{ts}')]]
    await context.bot.send_message(ADMIN_CHAT_ID, admin_msg, reply_markup=InlineKeyboardMarkup(buttons))
    await update.message.reply_text(trans('user_sent', uid, date=ds, time=ts), reply_markup=main_kb(uid))
    return ConversationHandler.END

async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd, cid, ds, ts = query.data.split('|')
    cid = int(cid)
    status = 'confirmed' if cmd == 'confirm' else 'denied'
    for r in to_notify.get(cid, []):
        if r['date']==ds and r['time']==ts:
            r['status']=status
            break
    text = (f"Your repair appointment on {ds} at {ts} is confirmed. See you then!" if status=='confirmed'
            else f"Sorry, your repair appointment on {ds} at {ts} was denied. Please try again or contact us.")
    await context.bot.send_message(cid, text)
    await query.edit_message_reply_markup(reply_markup=None)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(time_callback, pattern=r'^time\|')],
        states={ASK_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],ASK_PHONE:[MessageHandler(filters.CONTACT | filters.TEXT, ask_phone)]},
        fallbacks=[CallbackQueryHandler(callback_back_day, pattern=r'^back_day$')], per_chat=True
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('myid', myid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text))
    app.add_handler(CallbackQueryHandler(callback_lang, pattern=r'^lang\|'))
    app.add_handler(CallbackQueryHandler(callback_day, pattern=r'^day\|'))
    app.add_handler(CallbackQueryHandler(callback_back_day, pattern=r'^back_day$'))
    app.add_handler(CallbackQueryHandler(admin_response, pattern=r'^(confirm|deny)\|'))
    print('Bot started')
    app.run_polling()
