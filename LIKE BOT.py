# bot_fixed.py
import os
import re
import json
import aiohttp
from html import escape
from datetime import datetime, timedelta
import pytz

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# ---------------- CONFIG ----------------
# NOTE: rotate this token via @BotFather — it was pasted in plaintext and
# should be treated as compromised. Prefer loading from an environment
# variable instead of hardcoding it in source.
BOT_TOKEN = "8988399911:AAEAEOVXEMmo_xhKqC_NP_RKh7vP8QwtczY8"

API_VISIT_BASE = "https://sowi-visit-api-today-api.vercel.app"
API_LIKE_BASE = "https://like-api-by-ajay-one-last.vercel.app"
SPAM_API = "https://new-spam-ind-six.vercel.app"

ALLOWED_GROUP_ID = -1003997081680

OWNER_USERNAME = "agajayofficial"
OWNER_TELEGRAM_LINK = "https://t.me/agajayofficial"

# --- ADMIN(s) (telegram user IDs) ---
ADMINS = [8493811495]

# LIKE TRACKING - Track last like time per user
LIKE_TRACKING_FILE = "like_tracking.json"
RESET_HOUR = 4  # 4 AM
RESET_MINUTE = 30  # 4:30 AM

HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30)

# =====================================================================
# PREMIUM EMOJI SUPPORT (TEXT MESSAGES ONLY)
# =====================================================================

# ---- Placeholder emoji ----
PEM = {
    "ok": '<tg-emoji emoji-id="5260726538302660868">✅</tg-emoji>',
    "star": '<tg-emoji emoji-id="5258185631355378853">⭐️</tg-emoji>',
    "fire": '<tg-emoji emoji-id="5409139309309616640">🔥</tg-emoji>',
    "msg": '<tg-emoji emoji-id="5258215846450305872">💬</tg-emoji>',
    "user": '<tg-emoji emoji-id="5258362837411045098">👤</tg-emoji>',
    "money": '<tg-emoji emoji-id="5258204546391351475">💰</tg-emoji>',
    "lock": '<tg-emoji emoji-id="5258476306152038031">🔒</tg-emoji>',
    "pin": '<tg-emoji emoji-id="5258509201306557640">📍</tg-emoji>',
    "party": '<tg-emoji emoji-id="6041731551845159060">🎉</tg-emoji>',
    "sparkle": '<tg-emoji emoji-id="5778226250149532337">✨</tg-emoji>',
    "diamond": '<tg-emoji emoji-id="5359719332542718652">💎</tg-emoji>',
    "crown": '<tg-emoji emoji-id="5805553606635559688">👑</tg-emoji>',
    "heart": '<tg-emoji emoji-id="5258179403652801593">❤️</tg-emoji>',
    "arrow": '<tg-emoji emoji-id="5260450573768990626">➡️</tg-emoji>',
    "cross": '<tg-emoji emoji-id="5258226313285607065">❌</tg-emoji>',
    "warn": '<tg-emoji emoji-id="5409124594751660992">⚠️</tg-emoji>',
    "globe": '<tg-emoji emoji-id="5776233299424843260">🌐</tg-emoji>',
}

FALLBACK_EMOJI_ID = "6267008582294705964"
FALLBACK_LIST = ["✅", "❌", "⚠️", "⭐", "🔥", "💬", "👤", "💰", "🔒", "📍",
                  "🎉", "✨", "💎", "👑", "📱", "⚙️", "🔗", "❤️", "➡️", "👍", "👎"]

# NOTE: this dict has some duplicate keys (e.g. "1️⃣", "2️⃣", "⚠️", "💡",
# "✅️") defined twice with different premium emoji-ids further down. Python
# dict literals silently keep only the LAST value for a repeated key, so a
# few emoji may render with a different premium skin than you'd expect from
# reading top-to-bottom. Left intact to avoid breaking IDs you may be
# relying on — dedupe manually if a specific emoji looks wrong.
GLOBAL_BODY_EMOJIS = {
    "🔢": "5226513232549664618",
    "🖼": "5258050709252743821",
    "👤": "5258362837411045098",
    "⭐️": "5258185631355378853",
    "📂": "5258514780469075716",
    "❌": "5258226313285607065",
    "⚽️": "5258169263235013408",
    "🐻": "5258145898612924124",
    "📝": "5257965174979042426",
    "🪙": "5258368777350816286",
    "⚡️": "5258152182150077732",
    "📖": "5258328383183396223",
    "🤖": "5258093637450866522",
    "💼": "5258260149037965799",
    "👨‍🎨": "5258450450448915742",
    "🗓": "5258105663359294787",
    "🤙": "5258337316715373336",
    "📸": "5258205968025525531",
    "👩‍🎨": "5258215635996908355",
    "📣": "5260268501515377807",
    "✅": "5260726538302660868",
    "⛓": "5260730055880876557",
    "📄": "5258477770735885832",
    "©": "5258507474729704350",
    "👥": "5258513401784573443",
    "🗑": "5258130763148172425",
    "✍️": "5258331647358540449",
    "↔️": "5260233433107407649",
    "🎭": "5258430848218176413",
    "📁": "5257965810634202885",
    "➡️": "5260450573768990626",
    "🎮": "5258508428212445001",
    "🎓": "5258334872878980409",
    "❤️": "5258179403652801593",
    "🏘": "5257963315258204021",
    "🚪": "5258084656674250503",
    "💡": "5258216851472654189",
    "📍": "5258509201306557640",
    "🔒": "5258476306152038031",
    "💬": "5258215846450305872",
    "🌘": "5258011861273551368",
    "🎵": "5258289810082111221",
    "🔕": "5260264520080695245",
    "🎶": "5258334469152054985",
    "↗️": "5257991477358763590",
    "📌": "5258461531464539536",
    "✈️": "5258115571848846212",
    "➕": "5258108352008823107",
    "🍑": "5258330865674494479",
    "🔫": "5260221883940347555",
    "👏": "5258501105293205250",
    "🔄": "5258420634785947640",
    "🌠": "5258212268742549391",
    "🔃": "5260687681733533075",
    "⬅️": "5258236805890710909",
    "❗️": "5258474669769497337",
    "🤚": "5260249440450520061",
    "🗳": "5258200019495821936",
    "⬇️": "5258336354642697821",
    "🕔": "5258419835922030550",
    "⏲": "5258258882022612173",
    "👀": "5260341314095947411",
    "⬆️": "5260652420052032852",
    "🔼": "5260379144167890225",
    "💻": "5258423306255604960",
    "ℹ️": "5258503720928288433",
    "🙂": "5258262708838472996",
    "🔇": "5258267368877989660",
    "📈": "5258391025281408576",
    "☀️": "5258089153505009279",
    "📚": "5260512129240276089",
    "📦": "5258134813302332906",
    "✋": "5258362429389152256",
    "📹": "5258077307985207053",
    "📞": "5258020476977946656",
    "📼": "5258391252914676042",
    "🙃": "5258318251355545562",
    "🕘": "5199457120428249992",
    "🎙": "5260652149469094137",
    "💰": "5258204546391351475",
    "⚙": "5258096772776991776",
    "♾": "5271934788037517525",
    "📰": "5249231689695115145",
    "🏷": "5296348778012361146",
    "🔎": "5429571366384842791",
    "👁": "5253959125838090076",
    "⛔️": "5275969776668134187",
    "🔞": "5325604415900504150",
    "🍴": "5296727963495079440",
    "🔖": "5359629206948976159",
    "💎": "5359719332542718652",
    "🍏": "5775870512127283512",
    "🔣": "6035162669948867129",
    "🖥": "5942734685976138521",
    "⚙️": "5904258298764334001",
    "🎛": "5776424837786374634",
    "🗂": "5766994197705921104",
    "🔁": "6030657343744644592",
    "⏫": "5938437708635443119",
    "✏️": "6039779802741739617",
    "⌨": "6039404727542747508",
    "📎": "6039451237743595514",
    "🔧": "5962952497197748583",
    "🔨": "5940433880585605708",
    "🔓": "6037496202990194718",
    "📤": "6039573425268201570",
    "🛡": "6030537007350944596",
    "📥": "6041730074376410123",
    "📢": "6021418126061605425",
    "🔔": "6039486778597970865",
    "📷": "6030506650522096180",
    "🎞": "5944777041709633960",
    "🕓": "5775896410780079073",
    "👣": "5843679481566335204",
    "✅️": "5843596438373667352",
    "⏲️": "6037268453759389862",
    "🥇": "6037428784888549034",
    "🎥": "5886579539064132088",
    "🎤": "6030722571412967168",
    "☁": "6028115612163641653",
    "💭": "5904248647972820334",
    "💤": "5983401171501454028",
    "🗣": "6032653721853234759",
    "🎯": "6032949275732742941",
    "🎁": "6032644646587338669",
    "😀": "6043996047582170909",
    "😝": "6043847274210005137",
    "🤔": "6043960760130868895",
    "😐": "6041748912102968702",
    "😨": "6043973168291384891",
    "☹️": "6042029429301973188",
    "😡": "6044118213631938928",
    "🎉": "6041731551845159060",
    "👋": "6041921818896372382",
    "👍": "6041720006973067267",
    "👎": "6041716699848249286",
    "👆": "5886676966102274844",
    "✋️": "5891184096192763888",
    "🚫": "5938215362473496448", 
    "🍔": "6041874690220233085",
    "🎂": "5922305158636639117",
    "🛁": "6041963669057703997",
    "🏳️": "6041923781696426657",
    "🪧": "6042098561095570207",
    "⛱️": "6041933986538721961",
    "🗺": "5904650558127478452",
    "🏠": "6042137469204303531",
    "🏡": "5938537205847822613",
    "👓": "5882223295469722324",
    "⚪️": "5884332803016891855",
    "⬜️": "5884089033558070257",
    "☁️": "5884330496619450755",
    "#️⃣": "5924498929147189381",
    "🌝": "5938342819922973434",
    "🪟": "6035353688619356485",
    "⭕️": "5776428312414917091",
    "✨": "5778226250149532337",
    "🌙": "5769143090103193926",
    "🛜": "6048723247501938454",
    "💊": "6050677620830376838",
    "💧": "6050632433479455053",
    "🖍": "5771798621137670637",
    "🖌": "6050679691004612757",
    "🧽": "5811966564039135541",
    "🫥": "5812150667812280629",
    "🪄": "6021792097454002931",
    "🔡": "5771851822897566479",
    "🅰": "6030710030108463274",
    "✂️": "5771880672192893347",
    "📊": "5936143551854285132",
    "🌐": "5776233299424843260",
    "🏧": "5879814368572478751",
    "📅": "6267229004311303657",
    "🧠": "5864019342873598613",
    "🧭": "6030687898141987254",
    "🆕": "5895669571058142797",
    "🪐": "5891156376473836675",
    "4️⃣": "5411500398861118321",
    "3️⃣": "5409189019261103031",
    "2️⃣": "5411585799990830248",
    "1️⃣": "5408894951440279259",
    "🌟": "5805331990618053402",
    "🧩": "5837069325034331827",
    "🔍": "5460653580849541908",
    "🖌️": "5472305977447447589",
    "⭐": "5411211025439548989",
    "⚡": "5409212542796982248",
    "📉": "5411195254319637379",
    "🏪": "5418343793592135531",
    "🪶": "5425119010012296315",
    "👛": "5409150983030728043",
    "⚠️": "5409124594751660992",
    "🐳": "5461032508634199733",
    "🔥": "5409139309309616640",
    "🗑️": "5409324297846026427",
    "💲": "5409202131796255489",
    "🖼️": "5408889428112337556",
    "©️": "5408917074816820688",
    "0️⃣": "5411112902616706019",
}

def render_premium(text):
    """Convert placeholders + matching plain emoji into premium tg-emoji tags."""
    if not text:
        return str(text)

    text = str(text)

    for key, html_tag in PEM.items():
        placeholder = "{" + key + "}"
        if placeholder in text:
            text = text.replace(placeholder, html_tag)

    parts = re.split(r'(<tg-emoji.*?</tg-emoji>)', text)
    for i in range(len(parts)):
        if parts[i].startswith('<tg-emoji'):
            continue

        for normal_emj, prem_id in GLOBAL_BODY_EMOJIS.items():
            if normal_emj in parts[i]:
                parts[i] = parts[i].replace(
                    normal_emj,
                    f'<tg-emoji emoji-id="{prem_id}">{normal_emj}</tg-emoji>'
                )

        for emoji in FALLBACK_LIST:
            if emoji in parts[i] and f'>{emoji}</tg-emoji>' not in parts[i]:
                parts[i] = parts[i].replace(
                    emoji,
                    f'<tg-emoji emoji-id="{FALLBACK_EMOJI_ID}">{emoji}</tg-emoji>'
                )

    return "".join(parts)

# ---------------- LIKE TRACKING ----------------
def load_like_tracking():
    if not os.path.exists(LIKE_TRACKING_FILE):
        return {}
    try:
        with open(LIKE_TRACKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_like_tracking(data):
    with open(LIKE_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_today_reset_time():
    """Get today's reset time (4:30 AM) in IST"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    reset_time = now.replace(hour=RESET_HOUR, minute=RESET_MINUTE, second=0, microsecond=0)

    # If current time is before reset time, reset time is today's 4:30 AM
    # If current time is after reset time, reset time is tomorrow's 4:30 AM
    if now >= reset_time:
        reset_time = reset_time + timedelta(days=1)

    return reset_time

def can_user_like(user_id):
    """Check if user can use like command (once per day)"""
    tracking = load_like_tracking()
    user_id_str = str(user_id)

    if user_id_str not in tracking:
        return True

    last_used = tracking[user_id_str]
    try:
        last_used_dt = datetime.fromisoformat(last_used)
    except Exception:
        return True

    # Get today's reset time
    reset_time = get_today_reset_time()

    # Check if last used is before today's reset time
    if last_used_dt < reset_time:
        return True

    return False

def record_like_usage(user_id):
    """Record that user used like command"""
    tracking = load_like_tracking()
    tracking[str(user_id)] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
    save_like_tracking(tracking)

def get_next_reset_time():
    """Get human readable next reset time"""
    reset_time = get_today_reset_time()
    return reset_time.strftime("%I:%M %p")

# ---------------- GROUP CHECK ----------------
async def allow_group_only(update: Update):
    chat = update.effective_chat

    if chat.type == ChatType.PRIVATE:
        await update.message.reply_text(render_premium("❌ ᴛʜɪs ʙᴏᴛ ɪs ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ʜᴇʀᴇ."), parse_mode="HTML")
        return False

    if chat.id != ALLOWED_GROUP_ID:
        await update.message.reply_text(render_premium("❌ ᴛʜɪs ʙᴏᴛ ɪs ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ʜᴇʀᴇ."), parse_mode="HTML")
        return False

    return True

# ---------------------- START ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        "Lɪᴋᴇ | Vɪsɪᴛ | Sᴘᴀᴍ - ʙᴏᴛ:\n"
        "───────────────────\n"
        f"👤 Hᴇʟʟᴏ, {escape(user.first_name or '')}\n"
        "\n"
        "🤖 Wᴇʟᴄᴏᴍᴇ Tᴏ Fʀᴇᴇ Fɪʀᴇ Bᴏᴛ\n"
        "───────────────────\n"
        "\n"
        "ℹ️ BOT FEATURES !\n"
        "\n"
        "1️⃣ /like [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        " ╰ᐅ Sᴇɴᴅ ʟɪᴋᴇs ᴛᴏ ᴘʟᴀʏᴇʀ (1 ᴛɪᴍᴇ ᴘᴇʀ ᴅᴀʏ)\n"
        " ╰ᐅ Rᴇsᴇᴛ ᴛɪᴍᴇ: 4:30 AM IST\n"
        "\n"
        "2️⃣ /visit [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        " ╰ᐅ Sᴇɴᴅ ᴠɪsɪᴛs ᴛᴏ ᴘʟᴀʏᴇʀ (Uɴʟɪᴍɪᴛᴇᴅ)\n"
        "\n"
        "3️⃣ /spam [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        " ╰ᐅ Sᴇɴᴅ sᴘᴀᴍ ᴛᴏ ᴘʟᴀʏᴇʀ (Uɴʟɪᴍɪᴛᴇᴅ)\n"
        "\n"
        "4️⃣ /help\n"
        " ╰ᐅ Sʜᴏᴡ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴅᴇᴛᴀɪʟs\n"
        "───────────────────\n"
        "\n"
        "🌐 Sᴜᴘᴘᴏʀᴛᴇᴅ Rᴇɢɪᴏɴs !\n"
        " ╰ᐅ ɪɴᴅ, ʙʀ, ᴜs, sᴀᴄ, ɴᴀ, sɢ, ʀᴜ, ɪᴅ, ᴛᴡ, ᴠɴ, ᴛʜ, ᴍᴇ, ᴘᴋ, ʙᴅ, ᴇᴜ\n"
        "───────────────────\n"
        "❤️ ᴅᴇᴠ: ɢᴀʀᴇɴᴀ!"
    )

    await update.message.reply_text(render_premium(msg), parse_mode="HTML", disable_web_page_preview=True)

# ---------------------- HELP ----------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 𝗛𝗘𝗟𝗣 𝗖𝗘𝗡𝗧𝗘𝗥 !\n"
        "───────────────────\n"
        "\n"
        "ℹ️ Aʙᴏᴜᴛ ᴛʜɪs ʙᴏᴛ\n"
        "├─ 100% ꜰʀᴇᴇ & sᴇᴄᴜʀᴇ\n"
        "├─ 24/7 ᴀᴄᴛɪᴠᴇ & ʀᴜɴɴɪɴɢ\n"
        "├─ ɴᴏ ᴘʀᴏᴍᴏᴛɪᴏɴᴀʟ ᴀᴅs\n"
        "└─ ɴᴏ ꜰᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟ ᴊᴏɪɴ\n"
        "───────────────────\n"
        "\n"
        "⚡️ Cᴏᴍᴍᴀɴᴅꜱ ɢᴜɪᴅᴇ\n"
        "\n"
        "1️⃣ /like [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        " ├─ Sᴇɴᴅs ᴘʀᴏꜰɪʟᴇ ʟɪᴋᴇs\n"
        " ├─ ⚠️ 1 ᴛɪᴍᴇ ᴘᴇʀ ᴅᴀʏ (Rᴇsᴇᴛ ᴀᴛ 4:30 AM)\n"
        " └─  /like ind 123456789\n"
        "\n"
        "2️⃣ /visit [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        " ├─ Sᴇɴᴅs ᴘʀᴏꜰɪʟᴇ ᴠɪsɪᴛs\n"
        " ├─ 🔁 Uɴʟɪᴍɪᴛᴇᴅ ᴜsᴀɢᴇ\n"
        " └─  /visit ind 123456789\n"
        "\n"
        "3️⃣ /spam [ʀᴇɢɪᴏɴ] [ᴜɪᴅ]\n"
        " ├─ Sᴇɴᴅs ꜰʀɪᴇɴᴅ ʀᴇǫᴜᴇsᴛs\n"
        " ├─ 🔁 Uɴʟɪᴍɪᴛᴇᴅ ᴜsᴀɢᴇ\n"
        " └─  /spam ind 123456789\n"
        "───────────────────\n"
        "\n"
        "📝 ɪᴍᴘᴏʀᴛᴀɴᴛ ɴᴏᴛᴇ\n"
        "  ─────────────────────\n"
        "🔨 Aꜰᴛᴇʀ Gᴀʀᴇɴᴀ OB51 ᴜᴘᴅᴀᴛᴇ, ᴛʜᴇ ʟɪᴋᴇ sʏsᴛᴇᴍ ʜᴀs sᴏᴍᴇ ʟɪᴍɪᴛᴀᴛɪᴏɴs. Wᴇ ᴀʀᴇ ᴄᴏɴᴛɪɴᴜᴏsʟʏ ᴡᴏʀᴋɪɴɢ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ʙᴇsᴛ ᴇxᴘᴇʀɪᴇɴᴄᴇ.\n"
        "───────────────────\n"
        "❤️ ᴅᴇᴠ: ɢᴀʀᴇɴᴀ!"
    )

    await update.message.reply_text(render_premium(msg), parse_mode="HTML", disable_web_page_preview=True)

# ---------------------- LIKE COMMAND ----------------------
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allow_group_only(update):
        return

    user = update.effective_user

    if len(context.args) < 2:
        await update.message.reply_text(render_premium("⚠️ ᴜsᴀɢᴇ: /like ind uid"), parse_mode="HTML")
        return

    # Check if user can use like (once per day)
    if not can_user_like(user.id):
        next_reset = get_next_reset_time()
        await update.message.reply_text(
            render_premium(
                f"⏲️ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ʟɪᴋᴇ ᴛᴏᴅᴀʏ!\n"
                f"───────────────────\n"
                f"📅 Nᴇxᴛ ʀᴇsᴇᴛ ᴀᴛ: {next_reset} AM IST\n"
                f"───────────────────\n"
                f"💡 Tʀʏ ᴀɢᴀɪɴ ᴀꜰᴛᴇʀ ʀᴇsᴇᴛ!\n"
                f"❤️ ᴅᴇᴠ: ɢᴀʀᴇɴᴀ!"
            ),
            parse_mode="HTML"
        )
        return

    processing = await update.message.reply_text(
        render_premium("ᴘʀᴏᴄᴇssɪɴɢ ʟɪᴋᴇ..."),
        parse_mode="HTML"
    )

    region = context.args[0].lower()
    uid = context.args[1]

    api_url = f"{API_LIKE_BASE}/like?uid={uid}&server_name={region}"

    try:
        async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
            async with session.get(api_url) as resp:
                r = await resp.json(content_type=None)

        nickname = r.get("PlayerNickname", "-")
        before = r.get("LikesbeforeCommand", "-")
        after = r.get("LikesafterCommand", "-")
        added = r.get("LikesGivenByAPI", "-")
        status = r.get("status", 0)

        next_reset = get_next_reset_time()

        if status == 1:
            # Only spend the user's daily quota on a confirmed success —
            # a failed attempt (e.g. wrong UID, rate limited) shouldn't
            # cost them their one-per-day usage.
            record_like_usage(user.id)
            msg = (
                "✅ ʟɪᴋᴇ sᴜᴄᴄᴇssꜰᴜʟ\n"
                "───────────────────\n"
                f"👤 ᴘʟᴀʏᴇʀ: {escape(str(nickname))}\n"
                f"ℹ️ ᴜɪᴅ: <code>{escape(str(uid))}</code>\n"
                f"🌐 ʀᴇɢɪᴏɴ: {escape(region.upper())}\n"
                "\n"
                "📊 ʟɪᴋᴇs sᴛᴀᴛᴜs:\n"
                f"├─ ʙᴇꜰᴏʀᴇ: {before}\n"
                f"├─ ᴀꜰᴛᴇʀ: {after}\n"
                f"└─ ɢɪᴠᴇɴ: {added}\n"
                "\n"
                f"⏰ Nᴇxᴛ ʀᴇsᴇᴛ: {next_reset} AM\n"
                "───────────────────\n"
                "❤️ ᴅᴇᴠ: ɢᴀʀᴇɴᴀ!"
            )
        else:
            msg = (
                "✨ ʟɪᴋᴇ ꜰᴀɪʟᴇᴅ\n"
                "───────────────────\n"
                f"👤 ᴘʟᴀʏᴇʀ: {escape(str(nickname))}\n"
                f"ℹ️ ᴜɪᴅ: <code>{escape(str(uid))}</code>\n"
                f"🌐 ʀᴇɢɪᴏɴ: {escape(region.upper())}\n"
                "\n"
                "📊 ʟɪᴋᴇs sᴛᴀᴛᴜs:\n"
                f"├─ ʙᴇꜰᴏʀᴇ: {before}\n"
                f"├─ ᴀꜰᴛᴇʀ: {after}\n"
                f"└─ ɢɪᴠᴇɴ: {added}\n"
                "\n"
                "💡 ᴛʜɪs ᴀᴛᴛᴇᴍᴘᴛ ᴡᴀsɴ'ᴛ ᴄᴏᴜɴᴛᴇᴅ, ʏᴏᴜ ᴄᴀɴ ʀᴇᴛʀʏ.\n"
                "───────────────────\n"
                "❤️ ᴅᴇᴠ: ɢᴀʀᴇɴᴀ!"
            )

        await processing.edit_text(render_premium(msg), parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        await processing.edit_text(
            render_premium(
                "❗ᴀᴘɪ ᴇʀʀᴏʀ\n"
                "───────────────────\n"
                f"❌ ᴇʀʀᴏʀ: {escape(str(e))}\n"
                "───────────────────\n"
                "❤️ ᴅᴇᴠ: ɢᴀʀᴇɴᴀ!"
            ),
            parse_mode="HTML"
        )

# ---------------------- VISIT COMMAND ----------------------
async def visit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allow_group_only(update):
        return

    processing = await update.message.reply_text(
        render_premium("ᴘʀᴏᴄᴇssɪɴɢ ᴠɪsɪᴛ..."),
        parse_mode="HTML"
    )

    if len(context.args) < 2:
        await processing.edit_text(
            render_premium("⚠️ Usage: /visit <region> <uid>\n\nExample: /visit ind 6283999318"),
            parse_mode="HTML"
        )
        return

    reg
