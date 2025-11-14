# Day 2 Journal – SentinelGraph

## 📌 Overview
Day 2 focused on building SentinelGraph’s backend scraping architecture using Google Colab and the async-powered twscrape library. While Day 1 was about setting up the development environment, Day 2 established the technical foundation that will power all real Twitter scraping for the project.

This journal explains:
- What was done
- Why each step matters
- How the system changed
- What comes next

---

# 🧩 1. Moving Development Into Google Colab
We discovered that **Termux cannot run twscrape** because:

- Python 3.12 breaks lxml  
- Required system libraries are missing  
- twscrape is designed for PC/Colab environments  

So we moved scraping development entirely to **Google Colab**.

### ✔ Why this matters
Colab provides:
- Stable Python 3.10/3.11 environment  
- Async support  
- twscrape compatibility  
- Direct GitHub interaction  
- No dependency issues  

This ensures smooth development for backend scraping.

---

# 🧩 2. Cloning the SentinelGraph Repository in Colab
Command used:

```
!git clone https://github.com/USMANSARIB/SentinelGraph-mvp.git
```

This pulled the project into Colab’s filesystem.

### ✔ Why this matters
- We can edit backend files in real time  
- We can commit & push changes directly  
- Scraper code stays synced with GitHub  

---

# 🧩 3. Git User Configuration in Colab
Configured Git identity:

```
!git config --global user.name "USMANSARIB"
!git config --global user.email "ceusmansarib@gmail.com"
```

### ✔ Why this matters
Every commit is correctly attributed.

---

# 🧩 4. Creating Backend Project Structure
We created necessary folders:

```
!mkdir -p backend
!mkdir -p notebooks
!mkdir -p data/raw
```

### Folder purposes:
- **backend/** → scraper engine  
- **notebooks/** → scraping, testing, ML development  
- **data/raw/** → tweet datasets  

### ✔ Why this matters
This folder layout follows industry-standard ML project structures.

---

# 🧩 5. Implementing the Async Twitter Scraper
This was the core work of Day 2.

We created:

📁 `backend/scraper_twscrape.py`

containing:
- `TwitterScraper` (async)  
- `ScraperManager`  
- Normalization utilities  
- Parallel scraping support  
- tweet/user object cleaners  
- environment test function  

This is a **production-grade scraping engine**.

### ✔ Why this matters
twscrape is much faster and more stable than snscrape, supports:
- async scraping  
- multiple accounts  
- rate-limit-resistant  
- GraphQL Twitter API  

This makes SentinelGraph scalable.

---

# 🧩 6. Testing the Backend
We ran multiple tests:

### ✔ Backend exists
```
!ls backend
```

### ✔ Environment detection
```
test_environment()
```

Output:
```
{'twscrape_installed': True, 'ready_to_scrape': True}
```

### ✔ Class import test
```
from backend.scraper_twscrape import ScraperManager, TwitterScraper
```

Output:
```
Imports successful!
```

### ✔ Instance test
```
manager = ScraperManager()
```

Output:
```
ScraperManager ready: True
```

Everything is functioning correctly.

---

# 🧩 7. Why We Didn’t Scrape Today
Real scraping requires:

- Adding Twitter `auth_token` cookie  
- Logging into twscrape  
- Verifying session  
- Running async loops  

This is planned for **Day 3**, to keep the workflow clean and modular.

---

# 🟢 Summary of Day 2
You successfully:

- Set up development in Google Colab  
- Cloned your GitHub repo  
- Built clean backend folder structure  
- Added an advanced async scraper  
- Verified imports, environment, and architecture  
- Confirmed twscrape readiness  
- Prepared for real data collection  

### Day 2 is 100% complete.

---

# 🟣 What You Learned Today
- How async scraping works  
- Why twscrape is superior to snscrape  
- How to build backend architecture  
- How to run backend Python modules in Colab  
- How to normalize tweet/user objects  
- Why Termux isn’t suitable for advanced scraping  
- How to prepare for dataset creation  

---

# 🧭 Day 3 Preview
Day 3 will be exciting — we will perform the **first real scrape**.

You will:
- Add your Twitter cookie (`auth_token=...`)  
- Log in twscrape  
- Validate the account  
- Scrape 100–200 tweets  
- Save dataset to `data/raw/day3_scrape.json`  
- Journal everything  
- Commit it to GitHub  

---

# ✔ End of Day 2 Journal
Save this file as:

```
journal/day2.md
```
