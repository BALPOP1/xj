"""
signals.py
----------
Signal generation engine for the ZM Elite Bot Suite.

Produces realistic, randomised trading signals for two games:
  • Aviator  — crash-style multiplier game
  • Chicken Road 2 — obstacle-crossing game

All output is formatted with Telegram HTML tags (<b>, <code>, <i>) so
that bot files can send them safely using parse_mode="HTML".

The probability distributions are weighted to match realistic game
statistics (most rounds are low-to-medium, rare rounds are high).
"""

import random
from datetime import datetime


# ---------------------------------------------------------------------------
# Aviator Predator AI
# ---------------------------------------------------------------------------

def generate_aviator_signal() -> str:
    """
    Generates a randomised Aviator crash-game signal (HTML formatted).

    Uses a weighted distribution:
      • 50 % probability → low multiplier  (1.50 – 3.00x)
      • 35 % probability → mid multiplier  (3.01 – 7.00x)
      • 15 % probability → high multiplier (7.01 – 20.00x)

    Returns:
        str: A Telegram HTML-formatted signal message.
    """
    rand = random.random()

    if rand < 0.50:
        multiplier = round(random.uniform(1.50, 3.00), 2)
        confidence = random.randint(78, 91)
        risk_label = "🟢 LOW RISK"
        tip        = "Safe entry — ideal for conservative players."
    elif rand < 0.85:
        multiplier = round(random.uniform(3.01, 7.00), 2)
        confidence = random.randint(65, 80)
        risk_label = "🟡 MEDIUM RISK"
        tip        = "Good reward-to-risk ratio. Manage your bet size."
    else:
        multiplier = round(random.uniform(7.01, 20.00), 2)
        confidence = random.randint(50, 68)
        risk_label = "🔴 HIGH RISK"
        tip        = "Rare window — only bet what you can afford to lose."

    # Suggest cashing out slightly below the predicted peak for safety
    cashout   = round(multiplier * random.uniform(0.80, 0.90), 2)
    bet_pct   = random.choice(["10%", "15%", "20%", "25%"])
    timestamp = datetime.now().strftime("%H:%M:%S")

    return (
        "✈️ <b>ZM ELITE | AVIATOR PREDATOR AI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <b>Signal Time:</b> <code>{timestamp}</code>\n"
        f"🎯 <b>Predicted Multiplier:</b> <code>{multiplier}x</code>\n"
        f"💡 <b>Recommended Cashout:</b> <code>{cashout}x</code>\n"
        f"📊 <b>AI Confidence:</b> <code>{confidence}%</code>\n"
        f"⚠️  <b>Risk Level:</b> {risk_label}\n"
        f"💰 <b>Suggested Bet Size:</b> <code>{bet_pct} of balance</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 <i>{tip}</i>\n"
        "⚡ <i>Signal is time-sensitive — act on the next round!</i>\n"
        "🤖 <i>Powered by ZM Predator AI Engine</i>"
    )


# ---------------------------------------------------------------------------
# Chicken Road 2 Signal Bot
# ---------------------------------------------------------------------------

def generate_chicken_signal() -> str:
    """
    Generates a randomised Chicken Road 2 game signal (HTML formatted).

    Uses a weighted distribution:
      • 50 % probability → safe path   (3–5 obstacles,  1.50 – 3.50x)
      • 35 % probability → moderate    (6–9 obstacles,  3.51 – 8.00x)
      • 15 % probability → danger path (10–15 obstacles, 8.01 – 20.00x)

    Returns:
        str: A Telegram HTML-formatted signal message.
    """
    rand = random.random()

    if rand < 0.50:
        obstacles  = random.randint(3, 5)
        multiplier = round(random.uniform(1.50, 3.50), 2)
        path_label = "🟢 SAFE PATH"
        tip        = "Low risk — great for building your balance."
    elif rand < 0.85:
        obstacles  = random.randint(6, 9)
        multiplier = round(random.uniform(3.51, 8.00), 2)
        path_label = "🟡 MODERATE PATH"
        tip        = "Balanced play — stop when you hit the target multiplier."
    else:
        obstacles  = random.randint(10, 15)
        multiplier = round(random.uniform(8.01, 20.00), 2)
        path_label = "🔴 DANGER PATH"
        tip        = "High reward, high risk — experienced players only."

    confidence = random.randint(62, 93)
    bet_pct    = random.choice(["10%", "15%", "20%"])
    timestamp  = datetime.now().strftime("%H:%M:%S")

    return (
        "🐓 <b>SIGNAL-BOT | CHICKEN ROAD 2</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <b>Signal Time:</b> <code>{timestamp}</code>\n"
        f"🚦 <b>Path Prediction:</b> {path_label}\n"
        f"🏁 <b>Obstacles to Cross:</b> <code>{obstacles}</code>\n"
        f"💥 <b>Target Multiplier:</b> <code>{multiplier}x</code>\n"
        f"📊 <b>AI Confidence:</b> <code>{confidence}%</code>\n"
        f"💰 <b>Suggested Bet Size:</b> <code>{bet_pct} of balance</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 <i>{tip}</i>\n"
        "⚡ <i>Valid for next round only — do not delay!</i>\n"
        "🤖 <i>Powered by ZM Signal Engine</i>"
    )
