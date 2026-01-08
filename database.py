import sqlite3
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_NAME, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                amount REAL,
                status TEXT DEFAULT 'pending',
                chat_id INTEGER,
                admin_chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()
    
    def get_or_create_user(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            self.conn.commit()
            return self.get_or_create_user(user_id, username)
        
        return {
            'user_id': user[0],
            'username': user[1],
            'balance': user[2],
            'created_at': user[3]
        }
    
    def update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        self.conn.commit()
    
    def get_balance(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def add_product(self, name, price):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_products(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_product(self, product_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def create_order(self, user_id, product_id, amount):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO orders (user_id, product_id, amount, status) 
               VALUES (?, ?, ?, 'pending')''',
            (user_id, product_id, amount)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_orders(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT o.*, u.username, p.name as product_name 
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN products p ON o.product_id = p.id
            WHERE o.status = 'pending'
            ORDER BY o.created_at DESC
        ''')
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_order_chat(self, order_id, chat_id, admin_chat_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET chat_id = ?, admin_chat_id = ?, status = 'processing' WHERE id = ?",
            (chat_id, admin_chat_id, order_id)
        )
        self.conn.commit()
    
    def complete_order(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (order_id,)
        )
        self.conn.commit()
    
    def add_transaction(self, user_id, amount, tx_hash):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, amount, tx_hash) VALUES (?, ?, ?)",
            (user_id, amount, tx_hash)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_transaction_by_hash(self, tx_hash):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE tx_hash = ?", (tx_hash,))
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def update_transaction_status(self, tx_id, status):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE transactions SET status = ? WHERE id = ?",
            (status, tx_id)
        )
        self.conn.commit()
    
    def get_order_by_id(self, order_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT o.*, u.username, p.name as product_name 
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
        ''', (order_id,))
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def get_active_chats(self):
        """Получает активные чаты между пользователями и админом"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT o.user_id, u.username, o.chat_id, o.admin_chat_id
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'processing' AND o.chat_id IS NOT NULL
        ''')
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_user_chats(self, user_id):
        """Получает чаты пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT o.*, p.name as product_name
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ? AND o.status = 'processing'
            ORDER BY o.created_at DESC
        ''', (user_id,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_user_by_id(self, user_id):
        """Получает пользователя по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    
    def get_user_orders(self, user_id, status=None):
        """Получает заказы пользователя"""
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT o.*, p.name as product_name
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.user_id = ? AND o.status = ?
                ORDER BY o.created_at DESC
            ''', (user_id, status))
        else:
            cursor.execute('''
                SELECT o.*, p.name as product_name
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
            ''', (user_id,))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_orders(self, status=None):
        """Получает все заказы"""
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT o.*, u.username, p.name as product_name
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN products p ON o.product_id = p.id
                WHERE o.status = ?
                ORDER BY o.created_at DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT o.*, u.username, p.name as product_name
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN products p ON o.product_id = p.id
                ORDER BY o.created_at DESC
            ''')
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def delete_product(self, product_id):
        """Удаляет товар"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_product(self, product_id, name=None, price=None):
        """Обновляет товар"""
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if price is not None:
            updates.append("price = ?")
            params.append(price)
        
        if not updates:
            return False
        
        params.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_user_transactions(self, user_id):
        """Получает транзакции пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_users(self):
        """Получает всех пользователей"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            ORDER BY created_at DESC
        ''')
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_statistics(self):
        """Получает статистику"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        # Количество товаров
        cursor.execute("SELECT COUNT(*) FROM products")
        stats['total_products'] = cursor.fetchone()[0]
        
        # Общий баланс
        cursor.execute("SELECT SUM(balance) FROM users")
        total_balance = cursor.fetchone()[0]
        stats['total_balance'] = total_balance if total_balance else 0
        
        # Количество заказов по статусам
        cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        orders_by_status = cursor.fetchall()
        stats['orders_by_status'] = dict(orders_by_status)
        
        # Общая сумма заказов
        cursor.execute("SELECT SUM(amount) FROM orders WHERE status = 'completed'")
        total_sales = cursor.fetchone()[0]
        stats['total_sales'] = total_sales if total_sales else 0
        
        # Количество транзакций
        cursor.execute("SELECT COUNT(*) FROM transactions")
        stats['total_transactions'] = cursor.fetchone()[0]
        
        return stats

db = Database()