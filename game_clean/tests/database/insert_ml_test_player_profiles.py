from datetime import datetime
from game_clean.managers.PlayerProfileManager import PlayerProfileManager

def seed_test_players():
    ppm = PlayerProfileManager()

    test_players = {
        "test1": {  # Loose Aggressive (LAG)
            "hands_played": 1000,
            "vpip": 0.52,
            "pfr": 0.44,
            "aggression": 5.0,
            "showdown_freq": 0.28,
            "bluff_rate": 0.35,
            "avg_bet_size": 0.75
        },
        "test2": {  # Loose Passive (Calling Station)
            "hands_played": 1000,
            "vpip": 0.55,
            "pfr": 0.08,
            "aggression": 0.7,
            "showdown_freq": 0.48,
            "bluff_rate": 0.05,
            "avg_bet_size": 0.35
        },
        "test3": {  # Tight Passive (Nit / Rock)
            "hands_played": 1000,
            "vpip": 0.13,
            "pfr": 0.10,
            "aggression": 1.4,
            "showdown_freq": 0.22,
            "bluff_rate": 0.08,
            "avg_bet_size": 0.45
        }
    }

    for name, stats in test_players.items():
        # Force profile creation
        profile = ppm.get_profile(name)

        # Directly overwrite stats (no smoothing for test data)
        ppm.db.execute("""
            INSERT INTO player_profiles
            (name, hands_played, vpip, pfr, aggression, showdown_freq, bluff_rate, avg_bet_size, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                hands_played = excluded.hands_played,
                vpip = excluded.vpip,
                pfr = excluded.pfr,
                aggression = excluded.aggression,
                showdown_freq = excluded.showdown_freq,
                bluff_rate = excluded.bluff_rate,
                avg_bet_size = excluded.avg_bet_size,
                last_updated = excluded.last_updated
        """, (
            name,
            stats["hands_played"],
            stats["vpip"],
            stats["pfr"],
            stats["aggression"],
            stats["showdown_freq"],
            stats["bluff_rate"],
            stats["avg_bet_size"],
            datetime.now().isoformat()
        ))

        print(f"[OK] Inserted test profile: {name}")

if __name__ == "__main__":
    seed_test_players()
