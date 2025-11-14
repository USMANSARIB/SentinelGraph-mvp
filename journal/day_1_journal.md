# Day 1 Journal – SentinelGraph

This journal documents the full Day 1 setup of the SentinelGraph project in a narrative, clear, and beginner-friendly format. You can place this inside a `journal/day1.md` file in your repository.

---
## 📌 Overview
Day 1 focused entirely on **setting up the environment**, **configuring Git**, **generating SSH keys**, **connecting Termux to GitHub**, and **creating the initial project structure**. This day establishes the foundation that every future script, model, or feature will rely upon.

This journal explains:
- What you did
- Why each step matters
- What each command actually means
- What changed in your system during each step

---
## 🧩 1. Installing Termux
Termux is a Linux terminal that runs on Android. It gives access to commands like `git`, `python`, `nano`, package installations, and more.

**Why this matters:**
You turned your phone into a mini Linux development machine.

---
## 🧩 2. Updating Termux Packages
**Commands:**
```
pkg update -y
pkg upgrade -y
```
This updates Termux’s package index and upgrades outdated packages.

**Why:**
Prevents version conflicts later when installing tools like Python or Git.

During this step, you encountered a configuration file prompt (openssl). You safely chose **N** to keep the current configuration.

---
## 🧩 3. Installing Git
**Command:**
```
pkg install git -y
```
Git is installed on your device.

**Why:**
Git is essential for version control and interacting with GitHub.

You verified with:
```
git --version
```
---
## 🧩 4. Setting Git Identity
**Commands:**
```
git config --global user.name "USMANSARIB"
git config --global user.email "ceusmansarib@gmail.com"
```
These values are stored globally so Git knows who is making commits.

**Common issue:** Using curly quotes created a misconfigured email. You fixed this by removing and re-setting the email.

**Check configuration:**
```
git config --list
```
---
## 🧩 5. Creating Your SSH Key
**Command:**
```
ssh-keygen -t ed25519
```
This generated two files:
- `id_ed25519` → private key
- `id_ed25519.pub` → public key

**Why:** GitHub accepts SSH keys for authentication. It avoids password usage.

**View public key:**
```
cat ~/.ssh/id_ed25519.pub
```
You copied this key.

---
## 🧩 6. Adding SSH Key to GitHub
You added your public key via:
- GitHub app → Settings → SSH Keys → Add New Key

**Why:**
This lets GitHub confirm your identity when pushing code.

You tested it with:
```
ssh -T git@github.com
```
Expected message:
> "You've successfully authenticated..."
---
## 🧩 7. Cloning Your Repository
**Command:**
```
git clone git@github.com:USMANSARIB/SentinelGraph-mvp.git
```
Cloning downloaded the repository into Termux.

**Why this matters:**
This created the local project folder and connected it to GitHub.

---
## 🧩 8. Creating the Project Structure
Inside the repo:
```
mkdir backend
mkdir frontend
```
These folders organize your code:
- backend → Python scripts, APIs
- frontend → dashboard or UI

---
## 🧩 9. Creating & Editing README.md
You opened the file:
```
nano README.md
```
Nano shortcuts:
- **CTRL+X** → exit
- **Y** → save changes
- **Enter** → confirm filename

You filled in basic project description and goals.

---
## 🧩 10. Creating .gitignore
This prevents unwanted files from entering the repo.
```
__pycache__/
*.pyc
.env
node_modules/
venv/
```
This ensures your repo stays clean.

---
## 🧩 11. Staging, Committing & Pushing
You saved all changes:
```
git add .
git commit -m "Day 1: initial setup"
git push -u origin main
```
This uploaded your entire Day 1 work to GitHub.

---
## 🟢 Summary of What You Achieved Today
You successfully:
- Installed a Linux development environment
- Configured Git correctly
- Created and added SSH keys to GitHub
- Cloned your repo using secure SSH
- Created a professional backend/frontend folder structure
- Created README.md and .gitignore
- Committed and pushed the initial project state

**Day 1 is the hardest day — and you completed it fully.**

---
## 🟣 What You Learned
- How Linux package managers work
- How Git configuration works
- How SSH key-pair authentication works
- How GitHub recognizes devices
- Folder structuring in real-world software projects
- Using Nano efficiently for editing files
- Using Git to stage, commit, and push code

---
## 🧭 What Comes Next (Day 2 Preview)
- Installing snscrape
- Writing your first working scraper
- Saving JSON tweet data
- Printing structured output
- Committing scraper
- Creating Day 2 journal

Day 2 begins real code development.

---
## ✔ End of Day 1 Journal
This file can be saved as:
```
journal/day1.md
```

