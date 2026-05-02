import logging
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import PollType, ChatType

# Configuration
TOKEN = "8634875655"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_questions():
    """Loads questions from the JSON file."""
    try:
        with open("questions.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading questions: {e}")
        return []

def find_best_question(topic, questions):
    """Simple probabilistic search using keyword intersection."""
    topic_words = set(topic.lower().split())
    best_match = None
    highest_score = 0

    for q in questions:
        # Check keywords in question and explanation
        content = (q['question'] + " " + q.get('explanation', '')).lower()
        score = sum(1 for word in topic_words if word in content)
        
        if score > highest_score:
            highest_score = score
            best_match = q
            
    return best_match if highest_score > 0 else random.choice(questions)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start with interactive buttons."""
    keyboard = [
        [InlineKeyboardButton("🚀 Start Random Quiz", callback_data="quiz_random")],
        [InlineKeyboardButton("📚 About CryptoQuiz", callback_data="about_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💎 CryptoQuiz Pro\n\n"
        "Welcome! Ready to test your blockchain knowledge?\n\n"
        "💡 <b>Tip:</b> Use <code>/quiz [topic]</code> (e.g., <code>/quiz bitcoin</code>) to find specific questions!"
    )
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == "quiz_random":
        await query.edit_message_text("🔄 Finding a question for you...", parse_mode='Markdown')
        # We call the poll sender directly
        await send_quiz_logic(update, context)
    
    elif query.data == "about_bot":
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_start")]]
        await query.edit_message_text(
            "This bot provides professional crypto trivia. <blockquote>Use it in groups or privately to challenge yourself and your friends! Created by a passionate crypto enthusiast. 🚀</blockquote>",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
        
    elif query.data == "back_start":
        keyboard = [
            [InlineKeyboardButton("🚀 Start Random Quiz", callback_data="quiz_random")],
            [InlineKeyboardButton("📚 About CryptoQuiz", callback_data="about_bot")]
        ]
        await query.edit_message_text("💎 **CryptoQuiz Pro**\n\nChoose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /quiz [topic] command."""
    questions = load_questions()
    if not questions:
        await update.message.reply_text("⚠️ Database is empty.")
        return

    if context.args:
        topic = " ".join(context.args)
        quiz_data = find_best_question(topic, questions)
    else:
        quiz_data = random.choice(questions)

    await send_poll_to_chat(update, context, quiz_data)

async def send_quiz_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Helper for button-triggered quizzes."""
    questions = load_questions()
    if questions:
        quiz_data = random.choice(questions)
        await send_poll_to_chat(update, context, quiz_data)

async def send_poll_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, quiz_data):
    """The central logic to send the actual poll."""
    chat = update.effective_chat
    
    # Determine anonymity: Group polls must be public (not anonymous)
    # is_anonymous = False means users can see who voted what
    is_group = chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    
    await context.bot.send_poll(
        chat_id=chat.id,
        question=quiz_data["question"],
        options=quiz_data["options"],
        type=PollType.QUIZ,
        correct_option_id=quiz_data["correct_option_id"],
        explanation=quiz_data.get("explanation", "Study more!"),
        is_anonymous=not is_group if is_group else False # Public in groups
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("poll", quiz_command)) # Alias
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is live with Topic Search and Buttons...")
    application.run_polling()