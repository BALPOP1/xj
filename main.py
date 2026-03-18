"""
main.py
-------
Entry point for the ZM Elite Bot Suite.

Launches both bots concurrently:
  • ZM Elite | Aviator Predator AI
  • 💰 SIGNAL-BOT | CHICKEN ROAD 2 🐓

Each bot runs in its own daemon thread so that a crash in one bot does not
bring down the other.  The main thread blocks indefinitely by joining both
threads, keeping the process alive for Railway's "worker" dyno.
"""

import threading
import time

import aviator_bot
import chicken_bot


def _run_with_restart(target_fn, name: str) -> None:
    """
    Wraps a bot's run() function with automatic restart on unexpected crashes.

    If the bot's polling loop raises an unhandled exception, this wrapper
    waits 5 seconds and restarts it automatically, which is critical for
    long-running Railway deployments.

    Args:
        target_fn: The bot's run() function to call.
        name (str): Human-readable bot name used in log output.
    """
    while True:
        try:
            target_fn()
        except Exception as exc:
            print(f"❌ [{name}] crashed: {exc}. Restarting in 5 s...")
            time.sleep(5)


def main() -> None:
    """
    Starts both Telegram bots in separate daemon threads and keeps the
    main process alive until both threads terminate (which under normal
    operation they never do).
    """
    print("🚀 ZM Elite Bot Suite — starting both bots...")

    aviator_thread = threading.Thread(
        target=_run_with_restart,
        args=(aviator_bot.run, "Aviator"),
        daemon=True,
        name="AviatorBot",
    )

    chicken_thread = threading.Thread(
        target=_run_with_restart,
        args=(chicken_bot.run, "ChickenRoad"),
        daemon=True,
        name="ChickenRoadBot",
    )

    aviator_thread.start()
    chicken_thread.start()

    print("✅ Both bots are online. Monitoring threads...")

    # Block main thread — daemon threads keep running alongside it
    aviator_thread.join()
    chicken_thread.join()


if __name__ == "__main__":
    main()
