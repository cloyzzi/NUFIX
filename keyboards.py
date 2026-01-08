from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import Config

class Keyboards:
    def __init__(self):
        self.emojis = Config.EMOJIS
    
    def main_menu(self, is_admin=False):
        keyboard = [
            [KeyboardButton(f"{self.emojis['balance']} Баланс")],
            [KeyboardButton(f"{self.emojis['money']} Пополнить баланс")],
            [KeyboardButton(f"{self.emojis['phone']} Номера")]
        ]
        
        if is_admin:
            keyboard.append([KeyboardButton(f"{self.emojis['admin']} Админ панель")])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def admin_panel(self):
        keyboard = [
            [InlineKeyboardButton(f"{self.emojis['buy']} Добавить товар", callback_data="add_product")],
            [InlineKeyboardButton(f"{self.emojis['clock']} Заявки", callback_data="view_orders")],
            [InlineKeyboardButton(f"{self.emojis['money']} Выдать баланс", callback_data="give_balance")],
            [InlineKeyboardButton(f"{self.emojis['check']} Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def products_list(self, products):
        keyboard = []
        for product in products:
            button_text = f"{self.emojis['phone']} {product['name']} - {product['price']} TON"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"product_{product['id']}")])
        
        keyboard.append([InlineKeyboardButton(f"{self.emojis['check']} Назад", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    def product_detail(self, product_id):
        keyboard = [
            [
                InlineKeyboardButton(f"{self.emojis['buy']} Купить", callback_data=f"buy_{product_id}"),
                InlineKeyboardButton(f"{self.emojis['cross']} Назад", callback_data="back_to_products")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def payment_confirmation(self, order_id):
        keyboard = [
            [
                InlineKeyboardButton(f"{self.emojis['check']} Оплатил", callback_data=f"paid_{order_id}"),
                InlineKeyboardButton(f"{self.emojis['cross']} Отмена", callback_data="cancel_payment")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def order_actions(self, order_id):
        keyboard = [
            [
                InlineKeyboardButton(f"{self.emojis['check']} Выполнено", callback_data=f"complete_{order_id}"),
                InlineKeyboardButton(f"{self.emojis['cross']} Отклонить", callback_data=f"reject_{order_id}")
            ],
            [InlineKeyboardButton(f"{self.emojis['check']} Назад в админку", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def back_to_admin(self):
        keyboard = [[InlineKeyboardButton(f"{self.emojis['check']} Назад в админку", callback_data="admin_panel")]]
        return InlineKeyboardMarkup(keyboard)
    
    def back_to_products(self):
        keyboard = [[InlineKeyboardButton(f"{self.emojis['check']} Назад к товарам", callback_data="show_products")]]
        return InlineKeyboardMarkup(keyboard)
    
    def confirm_product_add(self):
        keyboard = [
            [
                InlineKeyboardButton(f"{self.emojis['check']} Да", callback_data="confirm_add"),
                InlineKeyboardButton(f"{self.emojis['cross']} Нет", callback_data="cancel_add")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def cancel_give_balance(self):
        keyboard = [[InlineKeyboardButton(f"{self.emojis['cross']} Отмена", callback_data="admin_panel")]]
        return InlineKeyboardMarkup(keyboard)

keyboards = Keyboards()