from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import logging

BOT_TOKEN = "8063909916:AAFMpmuasW0aeYmFtQvutoxPDUHm8sXijkE"
CHANNEL_USERNAME = "@rishabhearningtip"
YOUTUBE_LINK = "https://youtube.com/@rishabhearningtipss?si=4asSZyYDXpjTRTsh"
GROUP_CHAT_ID = -1002216818642  # Your group chat ID to send UPI and withdraw messages

MIN_WITHDRAW = 2
REFERRAL_BONUS = 1
MAX_REFERRAL_BONUS = 5

users_data = {}
claimed_users = set()
awaiting_upi = set()

logging.basicConfig(level=logging.INFO)

reply_keyboard = ReplyKeyboardMarkup(
    [
        ["💰 Balance", "🔗 Refer Link"],
        ["➕ Add UPI", "📤 Withdraw"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    args = context.args

    if user_id not in users_data:
        users_data[user_id] = {"balance": 1, "referrals": 0, "upi": None, "ref_bonus_earned": 0}

        if args:
            ref_id = args[0]
            if ref_id != user_id and ref_id in users_data:
                ref_user = users_data[ref_id]
                if ref_user["ref_bonus_earned"] < MAX_REFERRAL_BONUS:
                    ref_user["balance"] += REFERRAL_BONUS
                    ref_user["referrals"] += 1
                    ref_user["ref_bonus_earned"] += REFERRAL_BONUS

        keyboard = [
            [
                InlineKeyboardButton("Join", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
                InlineKeyboardButton("Join", url=YOUTUBE_LINK)
            ],
            [InlineKeyboardButton("✅ Claim Bonus", callback_data="claim_bonus")]
        ]

        await update.message.reply_text(
            "🚀 *Join all channels below then click Claim to get bonus:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("You already received your bonus.", reply_markup=reply_keyboard)

async def claim_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if user_id not in claimed_users:
        claimed_users.add(user_id)
        await query.message.reply_text("❌ Note: Please join all channels.")
    else:
        await query.message.reply_text("✅ Bonus Claimed! Start using menu below.", reply_markup=reply_keyboard)

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_upi
    user_id = str(update.effective_user.id)
    text = update.message.text

    if user_id in awaiting_upi:
        upi_id = text.strip()
        if "@" in upi_id and len(upi_id) >= 5:
            users_data[user_id]["upi"] = upi_id
            awaiting_upi.remove(user_id)
            await update.message.reply_text(f"✅ Your UPI ID '{upi_id}' has been saved!", reply_markup=reply_keyboard)

            # Send to group
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"New UPI ID from user {user_id}: {upi_id}"
            )
        else:
            await update.message.reply_text("❌ Invalid UPI ID format. Please send again.", reply_markup=reply_keyboard)
        return

    if text == "💰 Balance":
        data = users_data.get(user_id, {"balance": 0, "referrals": 0, "upi": None})
        await update.message.reply_text(f"Balance: ₹{data['balance']}\nReferrals: {data['referrals']}")

    elif text == "🔗 Refer Link":
        await update.message.reply_text(f"Refer link:\nhttps://t.me/instantuppi_bot?start={user_id}")

    elif text == "➕ Add UPI":
        awaiting_upi.add(user_id)
        await update.message.reply_text("Send your UPI ID now (e.g. yourname@bank).")

    elif text == "📤 Withdraw":
        data = users_data.get(user_id)
        if data is None:
            await update.message.reply_text("You don't have any balance yet. Start by /start command.", reply_markup=reply_keyboard)
            return
        if data["upi"] is None:
            await update.message.reply_text("Please add your UPI ID first using '➕ Add UPI' option.", reply_markup=reply_keyboard)
            return
        if data["balance"] < MIN_WITHDRAW:
            await update.message.reply_text(f"Minimum withdraw amount is ₹{MIN_WITHDRAW}. Earn more by referring.", reply_markup=reply_keyboard)
            return

        withdraw_amount = MIN_WITHDRAW
        data["balance"] -= withdraw_amount
        await update.message.reply_text(
            f"₹{withdraw_amount} withdrawal successful to your UPI ID: {data['upi']}\nCurrent Balance: ₹{data['balance']}",
            reply_markup=reply_keyboard
        )

        # Send to group
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"₹{withdraw_amount} withdrawal successful to UPI ID: {data['upi']}\nCurrent Balance: ₹{data['balance']}"
        )

    else:
        await update.message.reply_text("Please choose an option from the keyboard below.", reply_markup=reply_keyboard)

# Run Bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(claim_bonus, pattern="claim_bonus"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_buttons))

print("Bot running...")
app.run_polling()