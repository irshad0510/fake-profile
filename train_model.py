"""
train_model.py — Train the fake Instagram profile classifier

Usage:
  1. Download dataset from Kaggle:
     https://www.kaggle.com/datasets/free4ever1/instagram-fake-spammer-genuine-accounts
  2. Place train.csv and test.csv in the same folder as this script
  3. Run: python train_model.py
  4. Copy the generated model/model.pkl into your project root

Dataset columns expected:
  profile pic, nums/length username, fullname words, nums/length fullname,
  description length, external URL, private, #posts, #followers, #follows, fake
"""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading dataset...")

train_df = pd.read_csv("train.csv")
test_df  = pd.read_csv("test.csv")
df = pd.concat([train_df, test_df], ignore_index=True)

print(f"Total samples: {len(df)}")
print(f"Fake accounts: {df['fake'].sum()} | Real accounts: {(df['fake']==0).sum()}")

# ── Select features ────────────────────────────────────────────────────────────
FEATURES = [
    "profile pic",           # 1 = has pic
    "nums/length username",  # ratio of numbers in username
    "fullname words",        # word count in full name
    "description length",    # bio character length
    "external URL",          # 1 = has URL in bio
    "private",               # 1 = private account
    "#posts",                # number of posts
    "#followers",            # follower count
    "#follows",              # following count
]

TARGET = "fake"

X = df[FEATURES].fillna(0)
y = df[TARGET]

# ── Train/test split ──────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples")

# ── Train model ───────────────────────────────────────────────────────────────
print("\nTraining Random Forest classifier...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)

print(f"\n{'='*50}")
print(f"Accuracy:  {acc*100:.2f}%")
print(f"\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Real", "Fake"]))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Cross-validation
cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
print(f"\nCross-validation (5-fold): {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

# Feature importance
importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nFeature Importances:")
for feat, imp in importances.items():
    bar = "█" * int(imp * 40)
    print(f"  {feat:<30} {bar} {imp:.3f}")

# ── Save model ────────────────────────────────────────────────────────────────
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/model.pkl")
print(f"\nModel saved to model/model.pkl")
print("Copy this file into your project before deploying.")
