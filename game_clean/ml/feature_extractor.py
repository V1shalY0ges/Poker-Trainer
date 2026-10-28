# COMMENTS ARE DONE
import numpy as np

class FeatureExtractor:
    """
    Feature extractor for AdvancedBot compatible with 8-feature ML models.
    Features:
    1. equity
    2. pot
    3. bet_to_call
    4. pot_odds
    5. board_wetness
    6. vpip
    7. pfr
    8. aggression
    """

    def extract(self, equity, pot, bet_to_call, stack, vpip, pfr, aggression, board_wetness, position=None, stage=None):
        """
        Return a numpy array of 8 features for ML prediction.
        """
        # --- Pot odds ---
        pot_odds = bet_to_call / (pot + bet_to_call) if (pot + bet_to_call) > 0 else 0

        features = [
            equity,          # 1
            pot,             # 2
            bet_to_call,     # 3
            pot_odds,        # 4
            board_wetness,   # 5
            vpip,            # 6
            pfr,             # 7
            aggression       # 8
        ]

        return np.array(features, dtype=np.float32)
