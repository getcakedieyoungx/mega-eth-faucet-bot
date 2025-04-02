import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import requests
from anticaptchaofficial.turnstileproxyless import turnstileProxyless

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
        """Anti-Captcha ile Turnstile captcha çözümü"""
        solver = turnstileProxyless()
        solver.set_verbose(1)
        solver.set_key(self.anti_captcha_key)
        solver.set_website_url("https://testnet.megaeth.com")
        solver.set_website_key("0x4AAAAAAAHHhHHHhHHHhHHH")  # Cloudflare Turnstile site key
        
        print("Captcha çözülüyor...")
        token = solver.solve_and_return_solution()
        
        if token != 0:
            print(f"Captcha çözüldü: {token[:30]}...")
            return token
        else:
            print(f"Captcha çözülemedi: {solver.error_code}")
            return None
        
    def claim_faucet(self, wallet_address):
        """Faucet'ten ETH talep et"""
        headers = {
            'authority': 'carrot.megaeth.com',
            'accept': '*/*',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
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
        
        try:
            # Önce sayfayı ziyaret et
            session = requests.Session()
            session.get('https://testnet.megaeth.com')
            
            captcha_token = self.solve_captcha()
            if not captcha_token:
                return None
            
            data = {
                'address': wallet_address,
                'cf-turnstile-response': captcha_token
            }
            
            response = session.post(
                'https://carrot.megaeth.com/claim',
                headers=headers,
                json=data
            )
            
            print(f"Faucet yanıtı: {response.text}")
            
            if response.status_code == 200:
                print(f"Faucet başarıyla talep edildi: {response.json()}")
                return response.json()
            else:
                print(f"Faucet talebi başarısız: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Faucet talep hatası: {str(e)}")
            return None
        
    def transfer_eth(self, from_wallet, amount):
        """ETH'yi hedef adrese transfer et"""
        try:
            nonce = self.w3.eth.get_transaction_count(from_wallet['address'])
            
            gas_price = self.w3.eth.gas_price
            gas_limit = 21000
            
            transaction = {
                'nonce': nonce,
                'to': self.target_address,
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': 42069  # MegaETH Testnet Chain ID
            }
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                from_wallet['private_key']
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transfer işlemi gönderildi: {tx_hash.hex()}")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transfer tamamlandı: {receipt['transactionHash'].hex()}")
            return receipt
            
        except Exception as e:
            print(f"Transfer hatası: {str(e)}")
            return None
        
    def run(self, wallet_count):
        """Ana bot işlemini çalıştır"""
        print("Bot başlatılıyor...")
        
        if not self.anti_captcha_key:
            print("HATA: ANTI_CAPTCHA_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")
            return
            
        if not self.target_address:
            print("HATA: TARGET_ADDRESS bulunamadı. Lütfen .env dosyasını kontrol edin.")
            return
        
        # Yeni walletler oluştur
        self.create_wallets(wallet_count)
        
        # Her wallet için faucet claim et ve transfer yap
        for i, wallet in enumerate(self.wallets, 1):
            try:
                print(f"\nWallet {i}/{wallet_count} işleniyor: {wallet['address']}")
                
                # Faucet talep et
                print(f"Faucet talep ediliyor: {wallet['address']}")
                claim_result = self.claim_faucet(wallet['address'])
                
                if claim_result:
                    print("Bakiye kontrolü için bekleniyor (30 saniye)...")
                    time.sleep(30)  # Faucet işleminin tamamlanmasını bekle
                    
                    # Bakiyeyi kontrol et
                    balance = self.w3.eth.get_balance(wallet['address'])
                    balance_eth = self.w3.from_wei(balance, 'ether')
                    print(f"Güncel bakiye: {balance_eth} ETH")
                    
                    if balance > 0:
                        print(f"Transfer yapılıyor: {wallet['address']} -> {self.target_address}")
                        # Gas için biraz ETH bırak
                        transfer_amount = float(balance_eth) - 0.001
                        if transfer_amount > 0:
                            transfer_result = self.transfer_eth(wallet, transfer_amount)
                            if transfer_result:
                                print("Transfer başarılı!")
                        else:
                            print("Transfer için yetersiz bakiye.")
                    else:
                        print("Bakiye 0, transfer yapılmayacak.")
                
                # Rate limit için bekle
                print("Rate limit için bekleniyor (20 saniye)...")
                time.sleep(20)
                
            except Exception as e:
                print(f"Wallet işleme hatası: {str(e)}")
                continue
        
        print("\nTüm işlemler tamamlandı!")

if __name__ == "__main__":
    bot = MegaETHFaucetBot()
    bot.run(wallet_count=100)  # 100 wallet için çalıştır