# FakeGuard — Instagram Fake Profile Detector

A machine learning web app that detects fake Instagram profiles using 9 behavioral signals.
Built with pure HTML/CSS/JS frontend + Python serverless API, deployed on Vercel.

---

## Live Demo

Once deployed, your site will be at: `https://your-project-name.vercel.app`

---

## Project Structure

```
fake-profile-detector/
├── index.html          ← Frontend (main page)
├── style.css           ← Styles
├── script.js           ← Frontend logic + API call
├── vercel.json         ← Vercel deployment config
├── requirements.txt    ← Python dependencies
├── train_model.py      ← Script to train your ML model
├── api/
│   └── predict.py      ← Serverless API endpoint (/api/predict)
└── model/
    └── model.pkl       ← Trained model (generate with train_model.py)
```

---

## Step 1 — Train the ML Model (Local)

### Install dependencies
```bash
pip install scikit-learn pandas numpy joblib
```

### Get the dataset
1. Go to: https://www.kaggle.com/datasets/free4ever1/instagram-fake-spammer-genuine-accounts
2. Download `train.csv` and `test.csv`
3. Place them in the project root folder

### Train and save the model
```bash
python train_model.py
```

This generates `model/model.pkl`. Expected accuracy: ~92–95%.

---

## Step 2 — Deploy to Vercel via GitHub

### 1. Create GitHub repository
```bash
git init
git add .
git commit -m "Initial commit — FakeGuard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fake-profile-detector.git
git push -u origin main
```

> **Important:** Make sure `model/model.pkl` is committed if you want real ML predictions.
> If not committed, the app falls back to a heuristic scorer automatically.

### 2. Connect to Vercel
1. Go to https://vercel.com and sign in with GitHub
2. Click **"Add New Project"**
3. Import your `fake-profile-detector` repository
4. Framework preset: **Other**
5. Click **Deploy**

That's it! Vercel auto-detects `vercel.json` and deploys both static files and the Python API.

---

## How It Works

| Signal | Weight | Why |
|---|---|---|
| Profile picture | High | Fake accounts rarely set a pic |
| Numbers in username | High | Bots use random number strings |
| Follower/Following ratio | High | Bots follow many, have few followers |
| Post count | High | Fake accounts rarely post |
| Bio length | Medium | Real users write descriptions |
| Full name word count | Medium | Bot names are often single words |
| Account privacy | Low | Spam accounts are usually public |
| External URL in bio | Low | Often used for spam links |

---

## API Reference

**POST** `/api/predict`

Request body:
```json
{
  "followers": 120,
  "following": 890,
  "posts": 3,
  "bio": 0,
  "nums_in_username": 4,
  "fullname_words": 1,
  "profile_pic": 0,
  "is_private": 0,
  "has_external_url": 0
}
```

Response:
```json
{
  "fake": true,
  "score": 78,
  "confidence": 91,
  "signals": [
    { "text": "No profile picture", "warn": true },
    { "text": "Very low follower ratio", "warn": true }
  ],
  "source": "model"
}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JS |
| Backend API | Python (Vercel Serverless) |
| ML Model | Scikit-learn Random Forest |
| Dataset | Kaggle Instagram Fake Accounts |
| Hosting | Vercel |

---

## Notes

- The frontend works **without a backend** using a built-in heuristic scorer as fallback.
- To enable real ML predictions, commit `model/model.pkl` to your repo.
- The `model.pkl` file is typically ~5–15 MB — well within GitHub's 100 MB limit.
