# Retail Database Analytics

## Project Purpose

This project builds an end-to-end data pipeline that ingests raw retail transaction data from a CSV file, cleans and transforms it, loads it into a MySQL database, and runs analytical SQL queries to extract business insights. It demonstrates a real-world ETL (Extract, Transform, Load) workflow using Python's data ecosystem.

## Proje Amacı

Bu proje, ham perakende satış verisini CSV dosyasından okuyarak temizleyen, dönüştüren, MySQL veritabanına yükleyen ve iş zekası içgörüleri elde etmek için analitik SQL sorguları çalıştıran uçtan uca bir veri hattı (pipeline) oluşturur. Python veri ekosistemi kullanılarak gerçek dünya ETL (Extract, Transform, Load) iş akışını gösterir.

---

## Dataset Information

The dataset is the **Online Retail** dataset sourced from [Kaggle](https://www.kaggle.com/). It contains **540,000+** real-world e-commerce transaction records from a UK-based online retailer. The data intentionally includes real-world quality issues such as:

- Missing `CustomerID` values
- Zero or negative `Quantity` entries (returns/cancellations)
- Zero or negative `UnitPrice` values (invalid pricing)

These issues are handled and cleaned by the pipeline before loading into the database.

## Veri Seti Bilgisi

Veri seti, [Kaggle](https://www.kaggle.com/) platformundan alınan **Online Retail** veri setidir. İngiltere merkezli bir online perakendeciye ait **540.000+** gerçek e-ticaret işlem kaydı içerir. Veri, gerçek dünya kalite sorunlarını kasıtlı olarak barındırır:

- Eksik `CustomerID` değerleri
- Sıfır veya negatif `Quantity` kayıtları (iadeler/iptaller)
- Sıfır veya negatif `UnitPrice` değerleri (geçersiz fiyatlandırma)

Bu sorunlar, veritabanına yüklenmeden önce pipeline tarafından temizlenir.

---

## Technologies Used / Kullanılan Teknolojiler

| Technology / Teknoloji | Role / Rolü |
|---|---|
| **Python** | Core programming language / Ana programlama dili |
| **Pandas** | Data reading, cleaning & transformation / Veri okuma, temizleme ve dönüştürme |
| **MySQL** | Relational database storage / İlişkisel veritabanı depolama |
| **SQLAlchemy** | Database connection & SQL query execution / Veritabanı bağlantısı ve SQL sorgu yürütme |
| **PyMySQL** | MySQL driver for SQLAlchemy / SQLAlchemy için MySQL sürücüsü |
| **python-dotenv** | Secure credential management via `.env` / `.env` ile güvenli kimlik bilgisi yönetimi |

---

## How to Run / Nasıl Çalıştırılır

### 1. Download the dataset / Veri setini indir

Download the **Online Retail** dataset from [Kaggle](https://www.kaggle.com/datasets/vijayuv/onlineretail) and place the `data.csv` file in the project root directory.

**Online Retail** veri setini [Kaggle](https://www.kaggle.com/datasets/vijayuv/onlineretail) adresinden indirip `data.csv` dosyasını proje ana dizinine yerleştirin.

### 2. Install dependencies / Bağımlılıkları kur

```bash
pip install -r requirements.txt
```

### 3. Configure credentials / Kimlik bilgilerini yapılandır

Copy the example file and fill in your MySQL credentials:

`.env.example` dosyasını kopyalayıp MySQL bilgilerinizi girin:

```bash
cp .env.example .env
```

Then edit `.env` / Ardından `.env` dosyasını düzenleyin:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
```

### 4. Run the pipeline / Pipeline'ı çalıştır

```bash
python database_builder.py
```

---

## Output / Çıktı

The script prints the following analytics to the terminal after loading the data:

Script, veriyi yükledikten sonra aşağıdaki analizleri terminale yazdırır:

- **Top 5 Countries by Revenue** / Ciroya göre ilk 5 ülke
- **Top 5 Products by Quantity Sold** / Satış adedine göre ilk 5 ürün

### Terminal Screenshot / Terminal Ekran Görüntüsü
<img width="624" height="663" alt="Ekran görüntüsü 2026-04-24 184150" src="https://github.com/user-attachments/assets/18c2c3dd-ec0d-47e8-adb3-8f5ec14dc9b3" />


