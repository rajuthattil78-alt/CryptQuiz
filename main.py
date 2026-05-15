import logging
import json
import random
import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import PollType, ChatType, ParseMode

# Configuration
TOKEN = "8709169629:AAHpbVKjFHfC2IU5UJAsiC5DAIEw1o-JEJk"
LEADERBOARD_FILE = "leaderboard.json"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

COINS = [
    {"name": "Bitcoin", "ticker": "BTC", "hint": "The first decentralized cryptocurrency created in 2009."},
    {"name": "Ethereum", "ticker": "ETH", "hint": "A decentralized platform that runs smart contracts, created by Vitalik Buterin."},
    {"name": "Dogecoin", "ticker": "DOGE", "hint": "A cryptocurrency created as a joke in 2013 featuring a Shiba Inu dog."},
    {"name": "Binance Coin", "ticker": "BNB", "hint": "The native token of the largest cryptocurrency exchange by volume."},
    {"name": "Solana", "ticker": "SOL", "hint": "A high-performance blockchain known for extremely fast and cheap transactions."},
    {"name": "Ripple", "ticker": "XRP", "hint": "A digital payment network and protocol designed for fast cross-border transactions."},
    {"name": "Cardano", "ticker": "ADA", "hint": "A proof-of-stake blockchain platform founded by Charles Hoskinson."},
    {"name": "Tether", "ticker": "USDT", "hint": "The most widely used stablecoin pegged to the US Dollar."},
    {"name": "Chainlink", "ticker": "LINK", "hint": "A decentralized oracle network that provides real-world data to smart contracts."},
    {"name": "Polkadot", "ticker": "DOT", "hint": "A multi-chain protocol designed to facilitate cross-chain transfers of data and assets."}
]

def load_questions():
    try:
        with open("questions.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading questions: {e}")
        return []

def find_best_question(topic, questions):
    topic_words = set(topic.lower().split())
    best_match = None
    highest_score = 0

    for q in questions:
        content = (q['question'] + " " + q.get('explanation', '')).lower()
        score = sum(1 for word in topic_words if word in content)
        
        if score > highest_score:
            highest_score = score
            best_match = q
            
    return best_match if highest_score > 0 else random.choice(questions)

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    return {}

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def get_binance_data():
    symbols = '["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT"]'
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbols={symbols}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
    except Exception as e:
        logging.error(f"Binance API Error: {e}")
    return None

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎓 Start Crypto Quiz", callback_data="quiz_random"),
        InlineKeyboardButton("🎮 Guess the Coin", callback_data="game_guess")],
        [InlineKeyboardButton("📈 Live Analytics", callback_data="analytics_live"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard")],
        [InlineKeyboardButton("📚 About & Legal", callback_data="about_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 **Crypto Analytics & Education Dashboard**\n\n"
        "Welcome! This interactive dashboard allows you to explore the world of blockchain and cryptocurrency.\n\n"
        "🔸 **Test Your Knowledge**: Take randomized quizzes or use `/quiz <topic>` to learn about specific subjects.\n"
        "🔸 **Live Analytics**: Monitor real-time prices and 24h market movements for major cryptocurrencies.\n"
        "🔸 **Guess the Coin**: Play our exclusive mini-game to identify coins from technical hints.\n\n"
        "Please select a feature below to begin:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = load_questions()
    if not questions:
        await update.message.reply_text("⚠️ Database is empty.")
        return

    if context.args:
        topic = " ".join(context.args)
        quiz_data = find_best_question(topic, questions)
    else:
        quiz_data = random.choice(questions)

    chat = update.effective_chat
    is_group = chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    
    await context.bot.send_poll(
        chat_id=chat.id,
        question=quiz_data["question"],
        options=quiz_data["options"],
        type=PollType.QUIZ,
        correct_option_id=quiz_data["correct_option_id"],
        explanation=quiz_data.get("explanation", "Study more!"),
        is_anonymous=not is_group if is_group else False
    )

async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔒 **Privacy Policy**\n\n"
        "We are committed to your privacy. This bot only collects basic public Telegram profile information "
        "(User ID and First Name) strictly for the purpose of maintaining the game leaderboard. "
        "No other personal data is collected, stored, or shared."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 **Terms of Service**\n\n"
        "1. This bot is provided strictly for educational and analytical purposes.\n"
        "2. **We do not provide financial advice.** Do your own research before making any investment decisions.\n"
        "3. By using this bot, you agree that you are solely responsible for your own actions.\n"
        "4. Data is provided \"as is\" via public APIs and may not be completely accurate or real-time."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "quiz_random":
        await query.edit_message_text("🔄 Preparing your quiz module...")
        questions = load_questions()
        if questions:
            quiz_data = random.choice(questions)
            chat = update.effective_chat
            is_group = chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
            await context.bot.send_poll(
                chat_id=chat.id,
                question=quiz_data["question"],
                options=quiz_data["options"],
                type=PollType.QUIZ,
                correct_option_id=quiz_data["correct_option_id"],
                explanation=quiz_data.get("explanation", "Study more!"),
                is_anonymous=not is_group if is_group else False
            )
        else:
            await query.edit_message_text("⚠️ Database is currently unavailable. Please try again later.", reply_markup=main_menu_keyboard())

    elif data == "analytics_live":
        await query.edit_message_text("🔄 Fetching live data from Binance...")
        market_data = await get_binance_data()
        if market_data:
            text = "📈 **Live Market Analytics**\n\n"
            for coin in market_data:
                symbol = coin["symbol"].replace("USDT", "")
                price = float(coin["lastPrice"])
                change = float(coin["priceChangePercent"])
                emoji = "🟢" if change >= 0 else "🔴"
                text += f"**{symbol}**: ${price:,.2f} | {emoji} {change:+.2f}%\n"
            text += "\n_Data sourced from Binance API._"
            
            keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="back_start")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="back_start")]]
            await query.edit_message_text("⚠️ Unable to fetch market data at this time. Please try again later.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "game_guess":
        user_id = str(query.from_user.id)
        leaderboard = load_leaderboard()

        answered = []
        if user_id in leaderboard:
            answered = leaderboard[user_id].get("answered", [])

        available_coins = [c for c in COINS if c["ticker"] not in answered]
        # If user has answered all coins, reset their answered list and start over
        if not available_coins:
            if user_id in leaderboard:
                leaderboard[user_id]["answered"] = []
                save_leaderboard(leaderboard)
            available_coins = COINS.copy()

        coin = random.choice(available_coins)
        correct_ticker = coin["ticker"]

        all_tickers = [c["ticker"] for c in COINS if c["ticker"] != correct_ticker]
        options = random.sample(all_tickers, 3)
        options.append(correct_ticker)
        random.shuffle(options)

        text = (
            "🎮 **Guess the Coin**\n\n"
            f"**Hint:** {coin['hint']}\n\n"
            "Which coin is this?"
        )

        keyboard = []
        # Create 2 rows of 2 buttons
        keyboard.append([
            InlineKeyboardButton(options[0], callback_data=f"ans_{correct_ticker}_{options[0]}"),
            InlineKeyboardButton(options[1], callback_data=f"ans_{correct_ticker}_{options[1]}")
        ])
        keyboard.append([
            InlineKeyboardButton(options[2], callback_data=f"ans_{correct_ticker}_{options[2]}"),
            InlineKeyboardButton(options[3], callback_data=f"ans_{correct_ticker}_{options[3]}")
        ])
        keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="back_start")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("ans_"):
        parts = data.split("_")
        correct_ticker = parts[1]
        selected_ticker = parts[2]
        
        user_id = str(query.from_user.id)
        user_name = query.from_user.first_name
        leaderboard = load_leaderboard()
        if user_id not in leaderboard:
            leaderboard[user_id] = {"name": user_name, "score": 0, "answered": []}

        if selected_ticker == correct_ticker:
            leaderboard[user_id]["score"] += 10
            leaderboard[user_id]["name"] = user_name
            text = f"✅ **Correct!** It was {correct_ticker}.\n\nYou earned 10 points! Total score: {leaderboard[user_id]['score']}"
        else:
            text = f"❌ **Incorrect!** The right answer was {correct_ticker}.\n\nTry again to earn points!"

        # Mark this coin as answered for the user (counts whether they were correct or not)
        if "answered" not in leaderboard[user_id]:
            leaderboard[user_id]["answered"] = []
        if correct_ticker not in leaderboard[user_id]["answered"]:
            leaderboard[user_id]["answered"].append(correct_ticker)

        # If user answered all coins, reset the answered list so the pool restarts
        if len(leaderboard[user_id]["answered"]) >= len(COINS):
            leaderboard[user_id]["answered"] = []

        save_leaderboard(leaderboard)

        keyboard = [
            [InlineKeyboardButton("🎮 Play Again", callback_data="game_guess")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_start")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    elif data == "game_leaderboard":
        leaderboard = load_leaderboard()
        if not leaderboard:
            text = "🏆 **Leaderboard**\n\nNo scores yet! Be the first to play 'Guess the Coin'."
        else:
            # Sort by score descending
            sorted_board = sorted(leaderboard.values(), key=lambda x: x["score"], reverse=True)[:10]
            text = "🏆 **Top 10 Crypto Experts**\n\n"
            for i, user in enumerate(sorted_board, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                text += f"{medal} **{user['name']}**: {user['score']} pts\n"
                
        keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="back_start")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    elif data == "about_menu":
        text = (
            "📚 **About & Legal**\n\n"
            "This application provides educational quizzes and real-time market analytics to help you learn about blockchain technology.\n\n"
            "By using this bot, you agree to our policies. Use the commands below for more details:\n"
            "/privacy - View our Privacy Policy\n"
            "/terms - View our Terms of Service"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="back_start")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "back_start":
        await start(update, context)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("poll", quiz_command))
    application.add_handler(CommandHandler("privacy", privacy))
    application.add_handler(CommandHandler("terms", terms))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is live with compliance updates, Binance API, and Guess the Coin...")
    application.run_polling()