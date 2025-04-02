# MegaETH Faucet Bot

MegaETH Testnet için otomatik faucet talep ve transfer botu.

## Özellikler

- Otomatik wallet oluşturma
- Anti-Captcha entegrasyonu ile Cloudflare captcha çözümü
- Otomatik faucet talep etme
- Alınan ETH'leri belirlenen adrese transfer etme
- Hata yönetimi ve yeniden deneme mekanizması
- Detaylı loglama

## Kurulum

1. Repoyu klonlayın:
```bash
git clone https://github.com/yourusername/mega-eth-faucet-bot.git
cd mega-eth-faucet-bot
```

2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

3. `.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değerleri girin:
```bash
cp .env.example .env
```

4. `.env` dosyasını düzenleyin:
- `ANTI_CAPTCHA_KEY`: Anti-Captcha API anahtarınız
- `TARGET_ADDRESS`: ETH'lerin gönderileceği hedef adres

## Kullanım

Botu çalıştırmak için:

```bash
python bot.py
```

Bot varsayılan olarak 100 wallet oluşturacak ve her biri için:
1. Faucet'ten ETH talep edecek
2. Alınan ETH'leri belirlenen hedef adrese transfer edecek

## Güvenlik

- Private key'ler sadece geçici olarak memory'de tutulur
- Oluşturulan wallet'lar `wallets.json` dosyasına kaydedilir
- `.env` dosyası `.gitignore`'a eklenmiştir

## Notlar

- Rate limit'e takılmamak için işlemler arasında bekleme süreleri eklenmiştir
- Hata durumunda bot diğer wallet'larla devam eder
- Tüm işlemler loglanır