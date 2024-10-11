import json
import os
import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

TOKEN = "6464738786:AAHMT2Yfe-31k9QiluE5lVGsqtX633LvKqc"

application = Application.builder().token(TOKEN).build()

# Game options
SYMBOLS = {"X": "❌", "O": "⭕", "DOT": "•"}
THEMES = {
    "classic": {"X": "X", "O": "O", "DOT": "."},
    "emoji": {"X": "❌", "O": "⭕", "DOT": "•"},
    "space": {"X": "🚀", "O": "🪐", "DOT": "✨"},
    "fruit": {"X": "🍎", "O": "🍊", "DOT": "🍇"}
}

# Start command to choose difficulty
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    message = "Let's play Tic Tac Toe! Choose difficulty:"
    keyboard = [
        [InlineKeyboardButton("Easy", callback_data="difficulty_easy")],
        [InlineKeyboardButton("Medium", callback_data="difficulty_medium")],
        [InlineKeyboardButton("Hard", callback_data="difficulty_hard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

# Handle difficulty selection and ask for symbol preference
async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    difficulty = query.data.split("_")[1]
    chat_id = query.message.chat_id

    context.user_data['difficulty'] = difficulty

    # Ask for symbol preference
    message = f"Mode set to {difficulty.capitalize()}. Choose your symbol:"
    keyboard = [
        [InlineKeyboardButton("❌", callback_data="symbol_X"),
         InlineKeyboardButton("⭕", callback_data="symbol_O")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=message, reply_markup=reply_markup)

# Handle symbol selection and ask for theme
async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    symbol = query.data.split("_")[1]
    chat_id = query.message.chat_id

    context.user_data['player_symbol'] = symbol
    context.user_data['bot_symbol'] = "O" if symbol == "X" else "X"

    # Ask for theme
    message = f"You chose {SYMBOLS[symbol]}. Select a theme:"
    keyboard = [
        [InlineKeyboardButton("Classic", callback_data="theme_classic"),
         InlineKeyboardButton("Emoji", callback_data="theme_emoji")],
        [InlineKeyboardButton("Space", callback_data="theme_space"),
         InlineKeyboardButton("Fruit", callback_data="theme_fruit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=message, reply_markup=reply_markup)

# Handle theme selection and start game
async def handle_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    theme = query.data.split("_")[1]
    chat_id = query.message.chat_id

    context.user_data['theme'] = theme

    # Start the game
    reset_board(chat_id)
    await send_game_board(chat_id, context, query.message.message_id)

# Send game board
async def send_game_board(chat_id, context: ContextTypes.DEFAULT_TYPE, message_id=None):
    board = load_board(chat_id)
    theme = context.user_data.get('theme', 'classic')
    symbols = THEMES[theme]
    keyboard = [
        [InlineKeyboardButton(symbols[board[0]] if board[0] in symbols else symbols['DOT'], callback_data="0"),
         InlineKeyboardButton(symbols[board[1]] if board[1] in symbols else symbols['DOT'], callback_data="1"),
         InlineKeyboardButton(symbols[board[2]] if board[2] in symbols else symbols['DOT'], callback_data="2")],
        [InlineKeyboardButton(symbols[board[3]] if board[3] in symbols else symbols['DOT'], callback_data="3"),
         InlineKeyboardButton(symbols[board[4]] if board[4] in symbols else symbols['DOT'], callback_data="4"),
         InlineKeyboardButton(symbols[board[5]] if board[5] in symbols else symbols['DOT'], callback_data="5")],
        [InlineKeyboardButton(symbols[board[6]] if board[6] in symbols else symbols['DOT'], callback_data="6"),
         InlineKeyboardButton(symbols[board[7]] if board[7] in symbols else symbols['DOT'], callback_data="7"),
         InlineKeyboardButton(symbols[board[8]] if board[8] in symbols else symbols['DOT'], callback_data="8")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Tic Tac Toe"

    if message_id:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

# Reset game board
def reset_board(chat_id):
    board = ["", "", "", "", "", "", "", "", ""]
    save_board(chat_id, board)

# Save game board to file
def save_board(chat_id, board):
    with open(f"board_{chat_id}.json", "w") as f:
        json.dump(board, f)

# Load game board from file
def load_board(chat_id):
    if os.path.exists(f"board_{chat_id}.json"):
        with open(f"board_{chat_id}.json", "r") as f:
            return json.load(f)
    return ["", "", "", "", "", "", "", "", ""]

# Handle moves and update the board
async def handle_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    callback_data = query.data
    board = load_board(chat_id)
    player_symbol = context.user_data.get('player_symbol', 'X')
    bot_symbol = context.user_data.get('bot_symbol', 'O')

    if board[int(callback_data)] == "":
        board[int(callback_data)] = player_symbol  # Player move

        if check_winner(board, player_symbol):
            await context.bot.send_message(chat_id=chat_id, text=f"You win, <a href='tg://user?id={update.effective_user.id}'>{update.effective_user.first_name}</a>!", parse_mode="HTML")
            reset_board(chat_id)
            delete_user_file(chat_id)  # Delete user file on win
            await send_game_board(chat_id, context, message_id)
            return

        if is_board_full(board):
            await context.bot.send_message(chat_id=chat_id, text=f"It's a draw!")
            reset_board(chat_id)
            delete_user_file(chat_id)  # Delete user file on draw
            await send_game_board(chat_id, context, message_id)
            return

        difficulty = context.user_data.get('difficulty', 'easy')
        board = bot_move(board, difficulty, bot_symbol)

        if check_winner(board, bot_symbol):
            await context.bot.send_message(chat_id=chat_id, text=f"The bot wins!")
            reset_board(chat_id)
            delete_user_file(chat_id)  # Delete user file on loss
            await send_game_board(chat_id, context, message_id)
            return

        if is_board_full(board):
            await context.bot.send_message(chat_id=chat_id, text=f"It's a draw!")
            reset_board(chat_id)
            delete_user_file(chat_id)  # Delete user file on draw
            await send_game_board(chat_id, context, message_id)
            return

        save_board(chat_id, board)
        await send_game_board(chat_id, context, message_id)

# Check if player wins
def check_winner(board, player):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    return any(all(board[i] == player for i in combo) for combo in winning_combinations)

# Check if board is full
def is_board_full(board):
    return all(cell != "" for cell in board)

# Bot's move based on difficulty
def bot_move(board, difficulty, bot_symbol):
    if difficulty == "easy":
        return random_bot_move(board, bot_symbol)
    elif difficulty == "medium":
        return medium_bot_move(board, bot_symbol)
    elif difficulty == "hard":
        return hard_bot_move(board, bot_symbol)

# Random move for easy mode
def random_bot_move(board, bot_symbol):
    available_moves = [i for i, x in enumerate(board) if x == ""]
    if available_moves:
        move = random.choice(available_moves)
        board[move] = bot_symbol
    return board

# Medium difficulty logic
def medium_bot_move(board, bot_symbol):
    blocking_move = find_winning_move(board, bot_symbol)
    if blocking_move is not None:
        board[blocking_move] = bot_symbol
        return board
    return random_bot_move(board, bot_symbol)

# Hard difficulty logic
def hard_bot_move(board, bot_symbol):
    winning_move = find_winning_move(board, bot_symbol)
    if winning_move is not None:
        board[winning_move] = bot_symbol
        return board

    player_symbol = "X" if bot_symbol == "O" else "O"
    blocking_move = find_winning_move(board, player_symbol)
    if blocking_move is not None:
        board[blocking_move] = bot_symbol
        return board

    return random_bot_move(board, bot_symbol)

# Find winning move
def find_winning_move(board, symbol):
    for i in range(9):
        if board[i] == "":
            board[i] = symbol
            if check_winner(board, symbol):
                board[i] = ""
                return i
            board[i] = ""
    return None

# Delete user file
def delete_user_file(chat_id):
    if os.path.exists(f"board_{chat_id}.json"):
        os.remove(f"board_{chat_id}.json")

# Check user inactivity
async def check_inactivity(context: ContextTypes.DEFAULT_TYPE):
    while True:
        await context.bot.send_message(chat_id=YOUR_CHAT_ID, text="Checking for inactivity...")
        await asyncio.sleep(10)  # Check every 10 seconds

        # Logic to check if user is inactive goes here
        # This is a placeholder; implement your own inactivity detection logic

# Main function
def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_difficulty, pattern="difficulty"))
    application.add_handler(CallbackQueryHandler(handle_symbol, pattern="symbol"))
    application.add_handler(CallbackQueryHandler(handle_theme, pattern="theme"))
    application.add_handler(CallbackQueryHandler(handle_move, pattern="^[0-8]$"))

    application.run_polling()

if __name__ == "__main__":
    main()
