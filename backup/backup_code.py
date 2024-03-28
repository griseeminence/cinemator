async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)



# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Sends a message with three inline buttons attached."""
#     keyboard = [
#         [
#             InlineKeyboardButton("Option 1", callback_data="1"),
#             InlineKeyboardButton("Option 2", callback_data="2"),
#         ],
#         [InlineKeyboardButton("Option 3", callback_data="3")],
#     ]
#
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     await update.message.reply_text("Please choose:", reply_markup=reply_markup)
#
# async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Parses the CallbackQuery and updates the message text."""
#     query = update.callback_query
#
#     await query.answer()
#
#     await query.edit_message_text(text=f"Selected option: {query.data}")

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     name = requests.get(url_name_search, headers=headers).json()['docs'][0]['name']
#     id = requests.get(url_name_search, headers=headers).json()['docs'][0]['id']
#     year = requests.get(url_name_search, headers=headers).json()['docs'][0]['year']
#     description = requests.get(url_name_search, headers=headers).json()['docs'][0]['description']
#     poster =  requests.get(url_name_search, headers=headers).json()['docs'][0]['poster']
#     rating =  requests.get(url_name_search, headers=headers).json()['docs'][0]['rating']['kp']
#     message_text = f'{name}\n{year}\n{description}\n{rating}\n{poster}'
#     await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)