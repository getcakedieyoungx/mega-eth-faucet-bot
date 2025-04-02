import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import requests
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxyless

load_dotenv()

class MegaETHFaucetBot:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('https://rpc.testnet.megaeth.com'))
        self.anti_captcha_key = os.getenv('ANTI_CAPTCHA_KEY')
        self.target_address = os.getenv('TARGET_ADDRESS')
        self.wallets = []
        
    def create_wallets(self, count):
        """Belirtilen sayıda yeni wallet oluştur"""
        print(f"{count} adet yeni wallet oluşturuluyor...")
        for _ in range(count):
            account = Account.create()
            self.wallets.append({
                'address': account.address,
                'private_key': account.key.hex()
            })
            print(f"Wallet oluşturuldu: {account.address}")
        
        # Walletleri kaydet
        with open('wallets.json', 'w') as f:
            json.dump(self.wallets, f, indent=4)
            
    def solve_captcha(self):
        """Anti-Captcha ile Cloudflare captcha çözümü"""
        client = AnticaptchaClient(self.anti_captcha_key)
        task = NoCaptchaTaskProxyless(
            website_url="https://testnet.megaeth.com",
            website_key="CAPTCHA_SITE_KEY"  # Cloudflare captcha site key'i buraya gelecek
        )
        job = client.createTask(task)
        job.join()
        return job.get_solution_response()
        
    def claim_faucet(self, wallet_address):
        """Faucet'ten ETH talep et"""
        headers = {
            'authority': 'carrot.megaeth.com',
            'accept': '*/*',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://testnet.megaeth.com',
            'referer': 'https://testnet.megaeth.com/',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        
        captcha_token = self.solve_captcha()
        
        data = {
            'address': wallet_address,
            'captcha_token': captcha_token
        }
        
        response = requests.post(
            'https://carrot.megaeth.com/claim',
            headers=headers,
            json=data
        )
        
        return response.json()
        
    def transfer_eth(self, from_wallet, amount):
        """ETH'yi hedef adrese transfer et"""
        nonce = self.w3.eth.get_transaction_count(from_wallet['address'])
        
        transaction = {
            'nonce': nonce,
            'to': self.target_address,
            'value': self.w3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price
        }
        
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction,
            from_wallet['private_key']
        )
        
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
    def run(self, wallet_count):
        """Ana bot işlemini çalıştır"""
        # Yeni walletler oluştur
        self.create_wallets(wallet_count)
        
        # Her wallet için faucet claim et ve transfer yap
        for wallet in self.wallets:
            try:
                print(f"Faucet talep ediliyor: {wallet['address']}")
                claim_result = self.claim_faucet(wallet['address'])
                print(f"Faucet sonucu: {claim_result}")
                
                # Biraz bekle
                time.sleep(5)
                
                # Bakiyeyi kontrol et
                balance = self.w3.eth.get_balance(wallet['address'])
                if balance > 0:
                    print(f"Transfer yapılıyor: {wallet['address']} -> {self.target_address}")
                    transfer_result = self.transfer_eth(wallet, balance)
                    print(f"Transfer sonucu: {transfer_result}")
                
                # Rate limit için bekle
                time.sleep(10)
                
            except Exception as e:
                print(f"Hata oluştu: {str(e)}")
                continue

if __name__ == "__main__":
    bot = MegaETHFaucetBot()
    bot.run(wallet_count=100)  # 100 wallet için çalıştır