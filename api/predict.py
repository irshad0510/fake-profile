"""
Vercel Serverless Function — /api/predict
Receives profile data as JSON, returns fake/real classification.

Place this file at: api/predict.py
Vercel auto-routes POST /api/predict to this handler.
"""

import json
import os
import sys

def handler(request, response):
    """Vercel Python serverless handler."""

    # Only allow POST
    if request.method != 'POST':
        response.status_code = 405
        return response.send(json.dumps({"error": "Method not allowed"}))

    try:
        body = request.json
    except Exception:
        response.status_code = 400
        return response.send(json.dumps({"error": "Invalid JSON"}))

    # ── Extract features ──────────────────────────────────────────────────────
    followers         = int(body.get("followers", 0))
    following         = int(body.get("following", 0))
    posts             = int(body.get("posts", 0))
    bio               = int(body.get("bio", 0))
    nums_in_username  = int(body.get("nums_in_username", 0))
    fullname_words    = int(body.get("fullname_words", 1))
    profile_pic       = int(body.get("profile_pic", 0))        # 1 = has pic
    is_private        = int(body.get("is_private", 0))         # 1 = private
    has_external_url  = int(body.get("has_external_url", 0))   # 1 = has url

    # ── Try to load trained model ─────────────────────────────────────────────
    model_path = os.path.join(os.path.dirname(__file__), "..", "model", "model.pkl")

    if os.path.exists(model_path):
        # Real ML model prediction
        try:
            import joblib
            import numpy as np

            model = joblib.load(model_path)
            features = np.array([[
                profile_pic,
                nums_in_username,
                fullname_words,
                bio,
                is_private,
                has_external_url,
                posts,
                followers,
                following
            ]])

            prediction    = int(model.predict(features)[0])
            proba         = model.predict_proba(features)[0]
            fake_prob     = float(proba[1]) if len(proba) > 1 else float(proba[0])
            confidence    = round(max(proba) * 100, 1)
            score         = round(fake_prob * 100)

        except Exception as e:
            # Fall back to heuristics if model load fails
            score, prediction, confidence = heuristic_score(
                followers, following, posts, bio,
                nums_in_username, fullname_words,
                profile_pic, is_private, has_external_url
            )
    else:
        # No model found — use heuristic scorer
        score, prediction, confidence = heuristic_score(
            followers, following, posts, bio,
            nums_in_username, fullname_words,
            profile_pic, is_private, has_external_url
        )

    # ── Build signal list ─────────────────────────────────────────────────────
    ratio = (followers / following) if following > 0 else followers
    signals = build_signals(profile_pic, nums_in_username, posts, ratio,
                             bio, fullname_words, is_private, has_external_url)

    result = {
        "fake":       bool(prediction),
        "score":      score,
        "confidence": confidence,
        "signals":    signals,
        "source":     "model" if os.path.exists(model_path) else "heuristic"
    }

    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response.send(json.dumps(result))


# ── Heuristic scorer (used when no trained model is present) ──────────────────
def heuristic_score(followers, following, posts, bio,
                    nums, namewords, haspic, isprivate, hasurl):
    score = 0
    ratio = (followers / following) if following > 0 else followers

    if not haspic:     score += 22
    if nums >= 4:      score += 18
    elif nums >= 2:    score += 8
    if posts <= 2:     score += 18
    elif posts <= 10:  score += 8
    if ratio < 0.05:   score += 22
    elif ratio < 0.2:  score += 10
    if bio == 0:       score += 10
    if namewords <= 1: score += 8
    if hasurl:         score += 2

    score = min(score, 100)
    fake = score >= 45
    confidence = min(60 + score * 0.38, 98) if fake else min(60 + (100-score)*0.38, 97)
    return score, int(fake), round(confidence)


# ── Signal builder ────────────────────────────────────────────────────────────
def build_signals(haspic, nums, posts, ratio, bio, namewords, isprivate, hasurl):
    signals = []

    signals.append({"text": "Has profile picture", "warn": False} if haspic
                   else {"text": "No profile picture", "warn": True})

    if nums >= 4:    signals.append({"text": "Many numbers in username", "warn": True})
    elif nums >= 2:  signals.append({"text": "Some numbers in username", "warn": True})
    else:            signals.append({"text": "Clean username", "warn": False})

    if posts <= 2:   signals.append({"text": "Very few posts", "warn": True})
    elif posts <= 10:signals.append({"text": "Low post count", "warn": True})
    else:            signals.append({"text": "Adequate post count", "warn": False})

    if ratio < 0.05: signals.append({"text": "Very low follower ratio", "warn": True})
    elif ratio < 0.2:signals.append({"text": "Low follower ratio", "warn": True})
    else:            signals.append({"text": "Normal follower ratio", "warn": False})

    signals.append({"text": "Empty bio", "warn": True} if bio == 0
                   else {"text": "Bio present", "warn": False})

    signals.append({"text": "Single-word name", "warn": True} if namewords <= 1
                   else {"text": "Full name present", "warn": False})

    signals.append({"text": "Private account", "warn": False} if isprivate
                   else {"text": "Public account", "warn": False})

    if hasurl:
        signals.append({"text": "External URL in bio", "warn": True})

    return signals
