import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from config import Config
from handlers import bot_handlers
from admin import admin_handler, PRODUCT_NAME, PRODUCT_PRICE, GIVE_BALANCE_USER, GIVE_BALANCE_AMOUNT

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Создаем приложение
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Conversation handler для добавления товара
    add_product_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handler.start_add_product, pattern='^add_product$')],
        states={
            PRODUCT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handler.get_product_name),
                CallbackQueryHandler(admin_handler.cancel_add, pattern='^cancel_add$')
            ],
            PRODUCT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handler.get_product_price),
                CallbackQueryHandler(admin_handler.cancel_add, pattern='^cancel_add$')
            ],
        },
        fallbacks=[CallbackQueryHandler(admin_handler.cancel_add, pattern='^cancel_add$')],
    )
    
    # Conversation handler для выдачи баланса
    give_balance_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handler.start_give_balance, pattern='^give_balance$')],
        states={
            GIVE_BALANCE_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handler.get_user_for_balance),
                CallbackQueryHandler(admin_handler.cancel_give_balance, pattern='^cancel_add$')
            ],
            GIVE_BALANCE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handler.get_amount_for_balance),
                CallbackQueryHandler(admin_handler.cancel_give_balance, pattern='^cancel_add$')
            ],
        },
        fallbacks=[CallbackQueryHandler(admin_handler.cancel_give_balance, pattern='^cancel_add$')],
    )
    
    # Добавляем обработчики в правильном порядке
    application.add_handler(CommandHandler("start", bot_handlers.start))
    application.add_handler(add_product_handler)
    application.add_handler(give_balance_handler)
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(bot_handlers.show_product_detail, pattern='^product_'))
    application.add_handler(CallbackQueryHandler(bot_handlers.buy_product, pattern='^buy_'))
    application.add_handler(CallbackQueryHandler(bot_handlers.confirm_payment, pattern='^paid_'))
    application.add_handler(CallbackQueryHandler(bot_handlers.complete_order_admin, pattern='^complete_'))
    application.add_handler(CallbackQueryHandler(bot_handlers.reject_order_admin, pattern='^reject_'))
    application.add_handler(CallbackQueryHandler(bot_handlers.handle_callback))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_message))
    
    # Команды для админа
    application.add_handler(CommandHandler("chats", bot_handlers.handle_admin_message))
    application.add_handler(CommandHandler("reply", bot_handlers.handle_admin_message))
    
    # Запуск бота
    print(f"{Config.EMOJIS['pizza']} Pizza Numbers Bot запущен!")
    print(f"{Config.EMOJIS['admin']} Админ ID: {Config.ADMIN_ID}")
    print(f"{Config.EMOJIS['ton']} TON кошелек: {Config.WALLET_TON}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()