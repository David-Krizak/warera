from __future__ import annotations

import time

from playwright.sync_api import sync_playwright

from actions import perform_action
from game_selectors import LOOP_DELAY_SECONDS
from logic import choose_action
from readers import get_all_stats, debug_icon_stats
from session import open_game


def print_stats(stats) -> None:
    print("\n=== STATS ===")
    print(f"health: {stats.health}")
    print(f"eating: {stats.eating}")
    print(f"energy: {stats.energy}")
    print(f"selfwork: {stats.selfwork}")
    print(f"money: {stats.money}")
    print(f"level: {stats.level}")


def main() -> None:
    with sync_playwright() as playwright:
        context, page = open_game(playwright)

        try:
            debug_icon_stats(page)

            last_stats = None
            consecutive_failures = 0

            while True:
                try:
                    stats = get_all_stats(page)

                    if stats is None:
                        consecutive_failures += 1
                        print(f"[WARN] Stats not found this cycle. failures={consecutive_failures}")
                    else:
                        consecutive_failures = 0

                        if stats != last_stats:
                            print_stats(stats)
                            last_stats = stats

                        action = choose_action(stats)
                        if action is not None:
                            perform_action(page, action)
                        else:
                            print("[LOGIC] No action selected")

                except KeyboardInterrupt:
                    print("\n[INFO] Stopped by user")
                    break
                except Exception as e:
                    consecutive_failures += 1
                    print(f"[ERROR] Unexpected error: {e}")
                    print("[INFO] Stopping script due to error")
                    break

                print(f"[INFO] Sleeping {LOOP_DELAY_SECONDS} seconds...\n")
                time.sleep(LOOP_DELAY_SECONDS)

        finally:
            context.close()


if __name__ == "__main__":
    main()
