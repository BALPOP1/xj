"""
signals.py
----------
Signal generation engine for the ZM Elite Bot Suite.

Produces realistic, randomised trading signals for two games:
  • Aviator  — crash-style multiplier game
  • Chicken Road 2 — obstacle-crossing game

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
    Generates a randomised Aviator crash-game signal.

    Uses a weighted distribution:
      • 50 % probability → low multiplier  (1.50 – 3.00x)
      • 35 % probability → mid multiplier  (3.01 – 7.00x)
      • 15 % probability → high multiplier (7.01 – 20.00x)

    Returns:
        str: A Markdown-formatted signal message ready to be sent via Telegram.
    """
    rand = random.random()

    if rand < 0.50:
        multiplier  = round(random.uniform(1.50, 3.00), 2)
        confidence  = random.randint(78, 91)
        risk_label  = "🟢 LOW RISK"
        tip         = "Safe entry — ideal for conservative players."
    elif rand < 0.85:
        multiplier  = round(random.uniform(3.01, 7.00), 2)
        confidence  = random.randint(65, 80)
        risk_label  = "🟡 MEDIUM RISK"
        tip         = "Good reward-to-risk ratio. Manage your bet size."
    else:
        multiplier  = round(random.uniform(7.01, 20.00), 2)
        confidence  = random.randint(50, 68)
        risk_label  = "🔴 HIGH RISK"
        tip         = "Rare window — only bet what you can afford to lose."

    # Suggest cashing out slightly below the predicted peak for safety
    cashout    = round(multiplier * random.uniform(0.80, 0.90), 2)
    bet_pct    = random.choice(["10%", "15%", "20%", "25%"])
    timestamp  = datetime.now().strftime("%H:%M:%S")

    return (
        "✈️ *ZM ELITE | AVIATOR PREDATOR AI*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *Signal Time:* `{timestamp}`\n"
        f"🎯 *Predicted Multiplier:* `{multiplier}x`\n"
        f"💡 *Recommended Cashout:* `{cashout}x`\n"
        f"📊 *AI Confidence:* `{confidence}%`\n"
        f"⚠️  *Risk Level:* {risk_label}\n"
        f"💰 *Suggested Bet Size:* `{bet_pct} of balance`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 _{tip}_\n"
        "⚡ _Signal is time-sensitive — act on the next round!_\n"
        "🤖 _Powered by ZM Predator AI Engine_"
    )


# ---------------------------------------------------------------------------
# Chicken Road 2 Signal Bot
# ---------------------------------------------------------------------------

def generate_chicken_signal() -> str:
    """
    Generates a randomised Chicken Road 2 game signal.

    Uses a weighted distribution:
      • 50 % probability → safe path   (3–5 obstacles,  1.50 – 3.50x)
      • 35 % probability → moderate    (6–9 obstacles,  3.51 – 8.00x)
      • 15 % probability → danger path (10–15 obstacles, 8.01 – 20.00x)

    Returns:
        str: A Markdown-formatted signal message ready to be sent via Telegram.
    """
    rand = random.random()

    if rand < 0.50:
        obstacles   = random.randint(3, 5)
        multiplier  = round(random.uniform(1.50, 3.50), 2)
        path_label  = "🟢 SAFE PATH"
        tip         = "Low risk — great for building your balance."
    elif rand < 0.85:
        obstacles   = random.randint(6, 9)
        multiplier  = round(random.uniform(3.51, 8.00), 2)
        path_label  = "🟡 MODERATE PATH"
        tip         = "Balanced play — stop when you hit the target multiplier."
    else:
        obstacles   = random.randint(10, 15)
        multiplier  = round(random.uniform(8.01, 20.00), 2)
        path_label  = "🔴 DANGER PATH"
        tip         = "High reward, high risk — experienced players only."

    confidence = random.randint(62, 93)
    bet_pct    = random.choice(["10%", "15%", "20%"])
    timestamp  = datetime.now().strftime("%H:%M:%S")

    return (
        "🐓 *SIGNAL-BOT | CHICKEN ROAD 2*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *Signal Time:* `{timestamp}`\n"
        f"🚦 *Path Prediction:* {path_label}\n"
        f"🏁 *Obstacles to Cross:* `{obstacles}`\n"
        f"💥 *Target Multiplier:* `{multiplier}x`\n"
        f"📊 *AI Confidence:* `{confidence}%`\n"
        f"💰 *Suggested Bet Size:* `{bet_pct} of balance`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 _{tip}_\n"
        "⚡ _Valid for next round only — do not delay!_\n"
        "🤖 _Powered by ZM Signal Engine_"
    )
