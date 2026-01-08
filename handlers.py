from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import Config
from database import db
from keyboards import keyboards
from utils import ton_checker
import asyncio

class BotHandlers:
    def __init__(self):
        self.emojis = Config.EMOJIS
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db.get_or_create_user(user.id, user.username)
        
        welcome_text = f"""{self.emojis['pizza']} *Добро пожаловать в Pizza Numbers Bot!* {self.emojis['pizza']}

🍕 *Горячие номера Telegram как свежая пицца!*

{self.emojis['phone']} Покупайте качественные номера Telegram
{self.emojis['lock']} Полная анонимность и безопасность
{self.emojis['ton']} Оплата в TON - быстро и надежно
{self.emojis['check']} Автоматическая проверка платежей

👇 Выберите действие:"""
        
        is_admin = user.id == Config.ADMIN_ID
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboards.main_menu(is_admin),
            parse_mode='Markdown'
        )
    
    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        balance = db.get_balance(user_id)
        
        text = f"""{self.emojis['balance']} *Ваш баланс*
        
💰 Доступно: *{balance} TON*
{self.emojis['ton']} Кошелек: `{ton_checker.format_wallet_address()}`
        
👇 Используйте кнопку ниже для пополнения:"""
        
        await update.message.reply_text(
            text,
            reply_markup=keyboards.main_menu(update.effective_user.id == Config.ADMIN_ID),
            parse_mode='Markdown'
        )
    
    async def deposit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = f"""{self.emojis['money']} *Пополнение баланса*
        
{self.emojis['ton']} Отправьте TON на адрес:
`{Config.WALLET_TON}`

⚠️ *Внимание!*
1. Отправляйте ТОЛЬКО TON
2. Минимальная сумма: 0.1 TON
3. После отправки нажмите "Проверить оплату"
4. Система проверит платеж автоматически

📝 *Для проверки оплаты:*
1. Скопируйте хэш транзакции
2. Отправьте его боту в формате:
`check_0xваш_хэш`"""
        
        await update.message.reply_text(
            text,
            reply_markup=keyboards.main_menu(update.effective_user.id == Config.ADMIN_ID),
            parse_mode='Markdown'
        )
    
    async def check_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = update.message.text
        if message_text.startswith('check_'):
            tx_hash = message_text[6:].strip()
            
            if ton_checker.check_transaction(tx_hash):
                # Здесь должна быть логика проверки суммы и зачисления
                await update.message.reply_text(
                    f"{self.emojis['check']} Платеж найден! Ожидайте подтверждения...",
                    reply_markup=keyboards.main_menu(update.effective_user.id == Config.ADMIN_ID)
                )
            else:
                await update.message.reply_text(
                    f"{self.emojis['cross']} Платеж не найден или еще не подтвержден.",
                    reply_markup=keyboards.main_menu(update.effective_user.id == Config.ADMIN_ID)
                )
    
    async def show_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        products = db.get_products()
        
        if not products:
            text = f"{self.emojis['cross']} Товары временно отсутствуют!"
            await update.message.reply_text(
                text,
                reply_markup=keyboards.main_menu(update.effective_user.id == Config.ADMIN_ID)
            )
            return
        
        text = f"""{self.emojis['pizza']} *Наши номера* {self.emojis['pizza']}

👇 Выберите номер для покупки:"""
        
        await update.message.reply_text(
            text,
            reply_markup=keyboards.products_list(products),
            parse_mode='Markdown'
        )
    
    async def show_product_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            product_id = int(query.data.split('_')[1])
            product = db.get_product(product_id)
            
            if not product:
                await query.edit_message_text("❌ Товар не найден!")
                return
            
            # Генерируем описание товара
            description = self._generate_product_description(product)
            
            text = f"""{self.emojis['phone']} *{product['name']}*
            
{description}

💰 *Цена:* {product['price']} TON
🆔 *ID товара:* #{product['id']}
📅 *Добавлен:* {product['created_at']}

👇 Выберите действие:"""
            
            await query.edit_message_text(
                text,
                reply_markup=keyboards.product_detail(product_id),
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error in show_product_detail: {e}")
            await query.edit_message_text("❌ Произошла ошибка!")
    
    def _generate_product_description(self, product):
        """Генерирует описание товара на основе названия"""
        name_lower = product['name'].lower()
        
        descriptions = {
            'fresh': f"""🍕 *Свежий номер Telegram*
            
• Полностью новый аккаунт
• Никогда не использовался
• Полный доступ ко всем функциям
• Гарантия 30 дней
• Моментальная доставка""",
            
            'vip': f"""👑 *VIP номер Telegram*
            
• Премиум качество
• Приоритетная поддержка
• Дополнительные гарантии
• Быстрая активация
• Эксклюзивный сервис""",
            
            'premium': f"""💎 *Premium номер Telegram*
            
• Высшее качество
• Расширенная гарантия
• Персональный менеджер
• Быстрая доставка
• Полная анонимность""",
            
            'standard': f"""📱 *Стандартный номер Telegram*
            
• Надежный аккаунт
• Базовая гарантия
• Быстрая доставка
• Полный доступ
• Экономичный вариант"""
        }
        
        # Ищем ключевые слова в названии
        for key in descriptions:
            if key in name_lower:
                return descriptions[key]
        
        # Дефолтное описание
        return f"""📞 *Номер Telegram*
        
• Полный доступ к аккаунту
• Гарантия работоспособности
• Быстрая доставка
• Поддержка 24/7
• Анонимность и безопасность"""
    
    async def buy_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            product_id = int(query.data.split('_')[1])
            product = db.get_product(product_id)
            user_id = query.from_user.id
            
            if not product:
                await query.edit_message_text("❌ Товар не найден!")
                return
            
            # Создаем заказ
            order_id = db.create_order(user_id, product_id, product['price'])
            
            text = f"""{self.emojis['buy']} *Подтверждение покупки*
            
📱 Товар: {product['name']}
💰 Цена: {product['price']} TON
👤 Покупатель: @{query.from_user.username}
🆔 Заказ: #{order_id}

👇 Нажмите 'Оплатил' для продолжения:"""
            
            await query.edit_message_text(
                text,
                reply_markup=keyboards.payment_confirmation(order_id),
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error in buy_product: {e}")
            await query.edit_message_text("❌ Произошла ошибка!")
    
    async def confirm_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            order_id = int(query.data.split('_')[1])
            user = query.from_user
            
            # Получаем информацию о заказе
            order = db.get_order_by_id(order_id)
            
            if not order or order['user_id'] != user.id:
                await query.edit_message_text("❌ Заказ не найден!")
                return
            
            # Проверяем баланс
            balance = db.get_balance(user.id)
            if balance < order['amount']:
                await query.edit_message_text("❌ Недостаточно средств на балансе!")
                return
            
            # Списываем баланс
            db.update_balance(user.id, -order['amount'])
            
            # Обновляем статус заказа
            db.update_order_chat(order_id, user.id, Config.ADMIN_ID)
            
            # Создаем чат с админом - отправляем сообщение админу
            admin_chat_text = f"""📦 *Новая заявка!*
            
🆔 Заказ: #{order_id}
👤 Пользователь: @{user.username} (ID: {user.id})
📱 Товар: {order['product_name']}
💰 Сумма: {order['amount']} TON
⏰ Время: {order['created_at']}
            
👇 Обработайте заявку:"""
            
            # Отправляем сообщение админу
            try:
                await context.bot.send_message(
                    Config.ADMIN_ID,
                    admin_chat_text,
                    parse_mode='Markdown',
                    reply_markup=keyboards.order_actions(order_id)
                )
            except Exception as e:
                print(f"Error sending message to admin: {e}")
            
            # Сообщение пользователю об открытии чата
            user_text = f"""{self.emojis['check']} *Чат с администратором открыт!*
            
Здравствуйте, спасибо за покупку!
Администратор уже уведомлен о вашем заказе.

📞 *Чат открыт!* Вы можете общаться с администратором прямо здесь.

⏰ Время ожидания ответа не больше 24 часов.
            
👇 Администратор скоро свяжется с вами."""
            
            await query.edit_message_text(
                user_text,
                parse_mode='Markdown'
            )
            
            # Отправляем приветственное сообщение от имени бота в чат
            welcome_chat_text = f"""👋 *Чат с администратором*
            
🆔 Заказ: #{order_id}
📱 Товар: {order['product_name']}
💰 Сумма: {order['amount']} TON

Администратор получил уведомление о вашем заказе и скоро свяжется с вами для выдачи номера и кода.

Вы можете задавать вопросы прямо в этом чате."""
            
            await context.bot.send_message(
                user.id,
                welcome_chat_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error in confirm_payment: {e}")
            await query.edit_message_text("❌ Произошла ошибка при обработке платежа!")
    
    async def complete_order_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != Config.ADMIN_ID:
            await query.edit_message_text("⛔ Доступ запрещен!")
            return
        
        try:
            order_id = int(query.data.split('_')[1])
            order = db.get_order_by_id(order_id)
            
            if not order:
                await query.edit_message_text("❌ Заказ не найден!")
                return
            
            # Завершаем заказ
            db.complete_order(order_id)
            
            # Уведомляем пользователя
            try:
                await context.bot.send_message(
                    order['user_id'],
                    f"""{Config.EMOJIS['check']} *Ваш заказ выполнен!*
                    
🆔 Заказ: #{order_id}
📱 Товар: {order['product_name']}
✅ Статус: Выполнен

Спасибо за покупку! Если возникнут вопросы, обращайтесь.""",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            await query.edit_message_text(
                f"{Config.EMOJIS['check']} Заказ #{order_id} выполнен! Пользователь уведомлен.",
                reply_markup=keyboards.back_to_admin()
            )
        except Exception as e:
            print(f"Error in complete_order_admin: {e}")
            await query.edit_message_text("❌ Ошибка при выполнении заказа!")
    
    async def reject_order_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != Config.ADMIN_ID:
            await query.edit_message_text("⛔ Доступ запрещен!")
            return
        
        try:
            order_id = int(query.data.split('_')[1])
            order = db.get_order_by_id(order_id)
            
            if not order:
                await query.edit_message_text("❌ Заказ не найден!")
                return
            
            # Возвращаем деньги пользователю
            db.update_balance(order['user_id'], order['amount'])
            
            # Обновляем статус заказа
            cursor = db.conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = 'rejected' WHERE id = ?",
                (order_id,)
            )
            db.conn.commit()
            
            # Уведомляем пользователя
            try:
                await context.bot.send_message(
                    order['user_id'],
                    f"""{Config.EMOJIS['cross']} *Ваш заказ отклонен*
                    
🆔 Заказ: #{order_id}
📱 Товар: {order['product_name']}
💰 Возвращено: {order['amount']} TON
❌ Статус: Отклонен

Деньги возвращены на ваш баланс.""",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            await query.edit_message_text(
                f"{Config.EMOJIS['cross']} Заказ #{order_id} отклонен! Деньги возвращены пользователю.",
                reply_markup=keyboards.back_to_admin()
            )
        except Exception as e:
            print(f"Error in reject_order_admin: {e}")
            await query.edit_message_text("❌ Ошибка при отклонении заказа!")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            # Отправляем новое сообщение с главным меню
            user = query.from_user
            db.get_or_create_user(user.id, user.username)
            
            welcome_text = f"""{self.emojis['pizza']} *Главное меню* {self.emojis['pizza']}
            
👇 Выберите действие:"""
            
            is_admin = user.id == Config.ADMIN_ID
            await query.edit_message_text(
                welcome_text,
                reply_markup=keyboards.main_menu(is_admin),
                parse_mode='Markdown'
            )
            
        elif data == "admin_panel":
            from admin import admin_handler
            await admin_handler.admin_panel(update, context)
        elif data == "view_orders":
            from admin import admin_handler
            await admin_handler.view_orders(update, context)
        elif data == "add_product":
            from admin import admin_handler
            await admin_handler.start_add_product(update, context)
        elif data == "give_balance":
            from admin import admin_handler
            await admin_handler.start_give_balance(update, context)
        elif data == "show_products":
            await self.show_products(update, context)
        elif data == "back_to_products":
            await self.show_products(update, context)
        elif data.startswith("product_"):
            await self.show_product_detail(update, context)
        elif data.startswith("buy_"):
            await self.buy_product(update, context)
        elif data.startswith("paid_"):
            await self.confirm_payment(update, context)
        elif data.startswith("complete_"):
            await self.complete_order_admin(update, context)
        elif data.startswith("reject_"):
            await self.reject_order_admin(update, context)
        elif data == "cancel_payment":
            await query.edit_message_text(
                "❌ Покупка отменена.",
                reply_markup=keyboards.main_menu(query.from_user.id == Config.ADMIN_ID)
            )
        elif data == "cancel_add":
            # Обработка отмены добавления товара
            await query.edit_message_text(
                "❌ Добавление товара отменено.",
                reply_markup=keyboards.admin_panel()
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        
        # Проверяем, является ли пользователь админом
        is_admin = user_id == Config.ADMIN_ID
        
        if is_admin:
            # Если админ, обрабатываем через handle_admin_message
            await self.handle_admin_message(update, context)
            return
        
        # Логика для обычных пользователей
        if text == f"{Config.EMOJIS['balance']} Баланс":
            await self.show_balance(update, context)
        elif text == f"{Config.EMOJIS['money']} Пополнить баланс":
            await self.deposit(update, context)
        elif text == f"{Config.EMOJIS['phone']} Номера":
            await self.show_products(update, context)
        elif text.startswith('check_'):
            await self.check_payment(update, context)
        else:
            # Проверяем, есть ли у пользователя активные чаты с админом
            active_chats = db.get_user_chats(user_id)
            if active_chats:
                # Пересылаем сообщение админу
                for chat in active_chats:
                    try:
                        await context.bot.send_message(
                            Config.ADMIN_ID,
                            f"""📨 *Сообщение от пользователя*
                            
👤 Пользователь: @{update.effective_user.username} (ID: {user_id})
🆔 Заказ: #{chat['id']}
📱 Товар: {chat['product_name']}
💬 Сообщение: {text}""",
                            parse_mode='Markdown'
                        )
                        await update.message.reply_text(
                            f"{Config.EMOJIS['check']} Сообщение отправлено администратору!",
                            reply_markup=keyboards.main_menu(is_admin)
                        )
                    except Exception as e:
                        print(f"Error forwarding message to admin: {e}")
                        await update.message.reply_text(
                            "❌ Ошибка при отправке сообщения.",
                            reply_markup=keyboards.main_menu(is_admin)
                        )
            else:
                await update.message.reply_text(
                    "Используйте кнопки меню для навигации.",
                    reply_markup=keyboards.main_menu(is_admin)
                )
    
    async def handle_admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений от админа"""
        text = update.message.text
        
        # Проверяем кнопки главного меню
        if text == f"{Config.EMOJIS['balance']} Баланс":
            await self.show_balance(update, context)
        elif text == f"{Config.EMOJIS['money']} Пополнить баланс":
            await self.deposit(update, context)
        elif text == f"{Config.EMOJIS['phone']} Номера":
            await self.show_products(update, context)
        elif text == f"{Config.EMOJIS['admin']} Админ панель":
            from admin import admin_handler
            await admin_handler.admin_panel(update, context)
        elif text.startswith('check_'):
            await self.check_payment(update, context)
        # Проверяем, является ли это ответом на сообщение пользователя
        elif text.startswith('/reply '):
            try:
                parts = text.split(' ', 2)
                if len(parts) >= 3:
                    user_id = int(parts[1])
                    message = parts[2]
                    
                    # Отправляем сообщение пользователю
                    await context.bot.send_message(
                        user_id,
                        f"""📨 *Ответ от администратора*
                        
💬 {message}""",
                        parse_mode='Markdown'
                    )
                    
                    await update.message.reply_text(
                        f"{Config.EMOJIS['check']} Ответ отправлен пользователю!",
                        reply_markup=keyboards.main_menu(True)
                    )
                else:
                    await update.message.reply_text(
                        "❌ Неверный формат. Используйте: /reply <user_id> <сообщение>",
                        reply_markup=keyboards.main_menu(True)
                    )
            except Exception as e:
                print(f"Error sending reply: {e}")
                await update.message.reply_text(
                    "❌ Ошибка при отправке ответа.",
                    reply_markup=keyboards.main_menu(True)
                )
        elif text == "/chats":
            # Показать активные чаты
            active_chats = db.get_active_chats()
            if not active_chats:
                await update.message.reply_text(
                    "📭 Нет активных чатов.",
                    reply_markup=keyboards.main_menu(True)
                )
                return
            
            text_response = f"{Config.EMOJIS['clock']} *Активные чаты:*\n\n"
            for chat in active_chats:
                text_response += f"""👤 Пользователь: @{chat['username']} (ID: {chat['user_id']})
💬 Чат ID: {chat['chat_id']}
━━━━━━━━━━━━━━━━━━━━\n"""
            
            await update.message.reply_text(
                text_response,
                parse_mode='Markdown',
                reply_markup=keyboards.main_menu(True)
            )
        else:
            # Проверяем, есть ли у админа активные чаты
            active_chats = db.get_active_chats()
            if active_chats and not text.startswith('/'):
                # Если есть активные чаты и это не команда, предлагаем использовать /reply
                await update.message.reply_text(
                    "Для ответа пользователю используйте команду:\n"
                    "/reply <user_id> <сообщение>\n\n"
                    "Для просмотра активных чатов:\n"
                    "/chats",
                    reply_markup=keyboards.main_menu(True)
                )
            else:
                await update.message.reply_text(
                    "Используйте кнопки меню для навигации.",
                    reply_markup=keyboards.main_menu(True)
                )

bot_handlers = BotHandlers()