from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from config import Config
from database import db
from keyboards import keyboards

# States for conversation
PRODUCT_NAME, PRODUCT_PRICE = range(2)
GIVE_BALANCE_USER, GIVE_BALANCE_AMOUNT = range(2, 4)

class AdminHandler:
    def __init__(self):
        self.admin_id = Config.ADMIN_ID
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("⛔ Доступ запрещен!")
            return
        
        text = f"""{Config.EMOJIS['admin']} *Админ панель*
        
📊 Статистика:
• Пользователей: {self._get_users_count()}
• Товаров: {self._get_products_count()}
• Заявок: {self._get_pending_orders_count()}
• Баланс системы: {self._get_total_balance()} TON"""
        
        await update.message.reply_text(
            text,
            reply_markup=keyboards.admin_panel(),
            parse_mode='Markdown'
        )
    
    async def view_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != self.admin_id:
            await query.edit_message_text("⛔ Доступ запрещен!")
            return
        
        orders = db.get_pending_orders()
        
        if not orders:
            text = f"{Config.EMOJIS['check']} Нет активных заявок!"
            await query.edit_message_text(text, reply_markup=keyboards.back_to_admin())
            return
        
        text = f"{Config.EMOJIS['clock']} *Активные заявки:*\n\n"
        for order in orders:
            text += f"""📦 Заявка #{order['id']}
👤 Пользователь: @{order['username']}
📱 Товар: {order['product_name']}
💰 Сумма: {order['amount']} TON
⏰ Время: {order['created_at']}
━━━━━━━━━━━━━━━━━━━━\n"""
        
        await query.edit_message_text(
            text,
            reply_markup=keyboards.back_to_admin(),
            parse_mode='Markdown'
        )
    
    async def start_add_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != self.admin_id:
            await query.edit_message_text("⛔ Доступ запрещен!")
            return
        
        await query.edit_message_text(
            f"{Config.EMOJIS['buy']} Введите название товара:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_add")]])
        )
        return PRODUCT_NAME
    
    async def get_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['product_name'] = update.message.text
        
        await update.message.reply_text(
            f"{Config.EMOJIS['money']} Введите цену товара в TON:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_add")]])
        )
        return PRODUCT_PRICE
    
    async def get_product_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            price = float(update.message.text)
            name = context.user_data['product_name']
            
            db.add_product(name, price)
            
            await update.message.reply_text(
                f"{Config.EMOJIS['check']} Товар '{name}' успешно добавлен за {price} TON!",
                reply_markup=keyboards.admin_panel()
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ Неверная цена! Введите число.")
            return PRODUCT_PRICE
    
    async def start_give_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != self.admin_id:
            await query.edit_message_text("⛔ Доступ запрещен!")
            return
        
        await query.edit_message_text(
            f"{Config.EMOJIS['money']} Введите ID пользователя, которому хотите выдать баланс:",
            reply_markup=keyboards.cancel_give_balance()
        )
        return GIVE_BALANCE_USER
    
    async def get_user_for_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = int(update.message.text)
            context.user_data['give_balance_user_id'] = user_id
            
            # Проверяем существование пользователя
            cursor = db.conn.cursor()
            cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                username = user[0]
                await update.message.reply_text(
                    f"👤 Пользователь найден: @{username}\n"
                    f"{Config.EMOJIS['money']} Введите сумму в TON для выдачи:",
                    reply_markup=keyboards.cancel_give_balance()
                )
            else:
                await update.message.reply_text(
                    f"❌ Пользователь с ID {user_id} не найден.\n"
                    f"Попробуйте еще раз или нажмите 'Отмена':",
                    reply_markup=keyboards.cancel_give_balance()
                )
                return GIVE_BALANCE_USER
            
            return GIVE_BALANCE_AMOUNT
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный ID пользователя! Введите число.\n"
                "Попробуйте еще раз или нажмите 'Отмена':",
                reply_markup=keyboards.cancel_give_balance()
            )
            return GIVE_BALANCE_USER
    
    async def get_amount_for_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = float(update.message.text)
            user_id = context.user_data['give_balance_user_id']
            
            if amount <= 0:
                await update.message.reply_text(
                    "❌ Сумма должна быть больше 0!\n"
                    "Попробуйте еще раз или нажмите 'Отмена':",
                    reply_markup=keyboards.cancel_give_balance()
                )
                return GIVE_BALANCE_AMOUNT
            
            # Выдаем баланс
            db.update_balance(user_id, amount)
            
            # Получаем информацию о пользователе
            cursor = db.conn.cursor()
            cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            username = user[0] if user else "Неизвестно"
            
            # Отправляем уведомление пользователю
            try:
                await update._bot.send_message(
                    user_id,
                    f"{Config.EMOJIS['money']} *Вам выдан баланс!*\n\n"
                    f"💰 Сумма: *{amount} TON*\n"
                    f"👑 Выдал: администратор\n"
                    f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"Ваш текущий баланс: *{db.get_balance(user_id)} TON*",
                    parse_mode='Markdown'
                )
            except:
                pass  # Пользователь может не начать диалог с ботом
            
            await update.message.reply_text(
                f"{Config.EMOJIS['check']} Баланс успешно выдан!\n\n"
                f"👤 Пользователь: @{username} (ID: {user_id})\n"
                f"💰 Сумма: {amount} TON\n"
                f"✅ Новый баланс: {db.get_balance(user_id)} TON",
                reply_markup=keyboards.admin_panel()
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверная сумма! Введите число.\n"
                "Попробуйте еще раз или нажмите 'Отмена':",
                reply_markup=keyboards.cancel_give_balance()
            )
            return GIVE_BALANCE_AMOUNT
    
    async def cancel_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ Добавление товара отменено.",
            reply_markup=keyboards.admin_panel()
        )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel_give_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ Выдача баланса отменена.",
            reply_markup=keyboards.admin_panel()
        )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    def _get_users_count(self):
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    
    def _get_products_count(self):
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        return cursor.fetchone()[0]
    
    def _get_pending_orders_count(self):
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        return cursor.fetchone()[0]
    
    def _get_total_balance(self):
        cursor = db.conn.cursor()
        cursor.execute("SELECT SUM(balance) FROM users")
        result = cursor.fetchone()[0]
        return result if result else 0

admin_handler = AdminHandler()