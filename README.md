# Retail Database Analytics

## Project Purpose

This project is an end-to-end data science platform built around a real Turkish retail receipt dataset. It covers the full analytics lifecycle: an ETL pipeline that ingests transactional data from Excel into MySQL, SQL-based business analytics, and a machine learning module that forecasts the next 7 days of daily revenue using a Random Forest regressor.

## Proje Amacı

Bu proje, gerçek bir Türk perakende fiş verisi üzerine kurulu uçtan uca bir veri bilimi platformudur. Analitik yaşam döngüsünün tamamını kapsar: Excel'den MySQL'e veri aktaran ETL hattı, SQL tabanlı iş analitiği ve Random Forest regresyonu ile önümüzdeki 7 günün cirosunu tahmin eden bir makine öğrenmesi modülü.

---

## Dataset Information

The project uses a **real Turkish retail receipt dataset** covering **August 2023**. The store name is intentionally kept anonymous and the raw data file is **never** committed to GitHub for confidentiality.

**Dataset properties:**

- **9,921** transaction-level rows
- **31** consecutive days (01.08.2023 → 31.08.2023)
- **7** columns: `Cari Kod` (CustomerID), `Document No` (InvoiceNo), `Tarih` (Date), `Gender`, `Alt Sınıf1` (Category), `Net Adet` (Quantity), `Net TL` (Revenue)
- Categories include: `Denim All`, `Penye Üstler`, `Gömlek`, `Non Denim Altlar`, `Aksesuar`, etc.
- Gender segmentation: `Erkek`, `Kadın`, `Erkek Çocuk`, `Kız Çocuk`

## Veri Seti Bilgisi

Proje, **Ağustos 2023** dönemini kapsayan **gerçek bir Türk perakende fiş verisi** kullanır. Mağaza adı gizlilik gereği saklanmıştır ve ham veri dosyası gizlilik nedeniyle **GitHub'a asla yüklenmez**.

**Veri seti özellikleri:**

- **9.921** işlem bazlı satır
- **31** ardışık gün (01.08.2023 → 31.08.2023)
- **7** sütun: `Cari Kod`, `Document No`, `Tarih`, `Gender`, `Alt Sınıf1`, `Net Adet`, `Net TL`
- Kategoriler: `Denim All`, `Penye Üstler`, `Gömlek`, `Non Denim Altlar`, `Aksesuar` vb.
- Cinsiyet segmentasyonu: `Erkek`, `Kadın`, `Erkek Çocuk`, `Kız Çocuk`

---

## Technologies Used / Kullanılan Teknolojiler

| Technology / Teknoloji | Role / Rolü |
|---|---|
| **Python** | Core programming language / Ana programlama dili |
| **Pandas** | Data reading, cleaning & transformation / Veri okuma, temizleme ve dönüştürme |
| **openpyxl** | Excel (.xlsx) reading / Excel okuma |
| **MySQL** | Relational database storage / İlişkisel veritabanı depolama |
| **SQLAlchemy** | Database connection & SQL query execution / Veritabanı bağlantısı ve SQL sorguları |
| **PyMySQL + cryptography** | MySQL driver & secure auth / MySQL sürücüsü ve güvenli kimlik doğrulama |
| **python-dotenv** | Secure credential management via `.env` / `.env` ile güvenli kimlik bilgisi yönetimi |
| **Scikit-Learn** | Machine learning model training & evaluation / Makine öğrenmesi |
| **Matplotlib** | Data visualization & forecast plotting / Veri görselleştirme |
| **NumPy** | Numerical computing / Sayısal hesaplama |

---

## How to Run / Nasıl Çalıştırılır

### 1. Place your dataset / Veri setinizi yerleştirin

Place your `.xlsx` receipt file (e.g. `Ağustos 2023 Fiş Bilgisi.xlsx`) in the project root directory. The script auto-detects any `.xlsx` file in the folder.

`.xlsx` fiş dosyanızı (ör. `Ağustos 2023 Fiş Bilgisi.xlsx`) proje ana dizinine yerleştirin. Script klasördeki herhangi bir `.xlsx` dosyasını otomatik bulur.

> **Note:** The dataset itself is **never** pushed to GitHub (excluded via `.gitignore`).
>
> **Not:** Veri seti gizlilik nedeniyle **asla** GitHub'a gönderilmez (`.gitignore` ile hariç tutuldu).

### 2. Install dependencies / Bağımlılıkları kur

```bash
pip install -r requirements.txt
```

### 3. Configure credentials / Kimlik bilgilerini yapılandır

Copy the example env file and fill in your local MySQL credentials:

`.env.example` dosyasını kopyalayıp yerel MySQL bilgilerinizi girin:

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

### 4. Run the ETL pipeline / ETL hattını çalıştır

```bash
python database_builder.py
```

### 5. Run the ML forecaster / ML tahmin modelini çalıştır

```bash
python ml_forecaster.py
```

---

## Phase 1: ETL & SQL Analytics Output / ETL ve SQL Analitik Çıktısı

After loading the data into MySQL, the pipeline runs three analytical SQL queries and prints the results to the terminal:

Pipeline veriyi MySQL'e yükledikten sonra üç analitik SQL sorgusu çalıştırır ve sonuçları terminale yazdırır:

- **Top 5 Categories by Revenue** / Ciroya göre ilk 5 kategori (`Alt Sınıf1`)
- **Revenue Split by Gender** / Cinsiyete göre ciro dağılımı (`Erkek`, `Kadın`, `Erkek Çocuk`, `Kız Çocuk`)
- **Top 5 Customers by Revenue** / Ciroya göre ilk 5 müşteri (`Cari Kod`)

---

## Phase 2: AI & Time Series Forecasting

This phase uses the cleaned receipt data stored in MySQL to train a **RandomForestRegressor** (scikit-learn) that predicts the next **7 days** of daily revenue. The system extracts data via SQLAlchemy, engineers time-series features, trains the model, evaluates performance (MAE & R²), and generates a forecast chart.

**Feature Engineering:**
- `Day_of_Week` — Captures weekly seasonality patterns
- `Day_of_Month` — Captures intra-month patterns (e.g. payday effects)
- `Is_Weekend` — Binary weekend flag
- `Rolling_Mean_7d` — 7-day moving average to smooth fluctuations
- `Day_Index` — Numeric trend indicator

## Aşama 2: Yapay Zeka ve Gelecek Tahmini

Bu aşamada, MySQL'de saklanan temizlenmiş fiş verisi kullanılarak **RandomForestRegressor** (scikit-learn) modeli eğitilir ve önümüzdeki **7 günün** günlük cirosu tahmin edilir. Sistem SQLAlchemy ile veriyi çeker, zaman serisi özellikleri üretir, modeli eğitir, performansı değerlendirir (MAE & R²) ve tahmin grafiği oluşturur.

**Özellik Mühendisliği:**
- `Day_of_Week` — Haftalık mevsimsellik kalıpları
- `Day_of_Month` — Ay içi kalıplar (maaş günü etkisi vb.)
- `Is_Weekend` — İkili hafta sonu bayrağı
- `Rolling_Mean_7d` — Dalgalanmaları düzleştiren 7 günlük hareketli ortalama
- `Day_Index` — Sayısal trend göstergesi

### Forecast Output / Tahmin Çıktısı

![Revenue Forecast Chart](forecast_output.png)

---

## Privacy & Security / Gizlilik ve Güvenlik

- The real sales dataset is **never** committed to this repository.
- `.gitignore` blocks all `.csv`, `.xlsx`, and `.xls` files from being pushed.
- MySQL credentials are stored only in a local `.env` file, also excluded by `.gitignore`.
- The store name behind the dataset is anonymized.

- Gerçek satış verisi bu repoya **asla** dahil edilmez.
- `.gitignore`, tüm `.csv`, `.xlsx` ve `.xls` dosyalarının push'lanmasını engeller.
- MySQL kimlik bilgileri yalnızca yerel `.env` dosyasında tutulur, o da `.gitignore` ile dışlanır.
- Veri setinin ait olduğu mağaza adı gizli tutulmuştur.
