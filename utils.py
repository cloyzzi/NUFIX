import requests
import time
from config import Config

class TONChecker:
    def __init__(self):
        self.api_key = Config.TONCENTER_API_KEY
        self.api_url = Config.TONCENTER_API_URL
        self.wallet_address = Config.WALLET_TON
    
    def check_transaction(self, tx_hash):
        """Проверяет транзакцию по хэшу"""
        try:
            headers = {'X-API-Key': self.api_key}
            params = {'hash': tx_hash}
            
            response = requests.get(
                f"{self.api_url}getTransaction",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('ok', False)
        except Exception as e:
            print(f"Error checking transaction: {e}")
        
        return False
    
    def get_wallet_transactions(self, limit=10):
        """Получает последние транзакции кошелька"""
        try:
            headers = {'X-API-Key': self.api_key}
            params = {
                'address': self.wallet_address,
                'limit': limit
            }
            
            response = requests.get(
                f"{self.api_url}getTransactions",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json().get('result', [])
        except Exception as e:
            print(f"Error getting transactions: {e}")
        
        return []
    
    def format_wallet_address(self):
        """Форматирует адрес кошелька для отображения"""
        if len(self.wallet_address) > 20:
            return f"{self.wallet_address[:10]}...{self.wallet_address[-10:]}"
        return self.wallet_address

ton_checker = TONChecker()