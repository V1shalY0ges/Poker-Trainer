from collections import defaultdict
from itertools import combinations

#each poker hand is unique so it needs its own method

class HandEvaluator():
    HAND_RANKS = {
        "Royal Flush": 10,
        "Straight Flush": 9,
        "Four of a Kind": 8,
        "Full House": 7,
        "Flush": 6,
        "Straight": 5,
        "Three of a Kind": 4,
        "Two Pair": 3,
        "One Pair": 2,
        "High Card": 1,
    }



    def count_hole_cards(self, cards, hole):
        #
        #NEED TO CHANGE THIS HERE AS NO LONGER NEEDED
        #
        #
        #
        #

        """Count how many cards from 'cards' are in the hole cards."""
        return sum(1 for card in cards if card in hole)

    def get_rank_groups(self, cards):
        rank_groups = defaultdict(list)
        for card in cards:
            rank = card[:-1]
            rank_groups[rank].append(card)
        return rank_groups


    # Try each hand check; if it returns cards (not None), return the hand name and cards
    def evaluate_hand(self, hole_cards, community_cards):
        #
        #
        #NO NEED TO PASS IN THE HOLE CARDS HERE JUST PASS IN THE FULL SET OF CARDS
        #
        #
        #
        hole = hole_cards
        #print(f"HOLE FOR EVALUATE HAND: {hole}")
        hand_cards = hole_cards + community_cards
        #print(hand_cards)
        ace_low = False

        rf_result= self.royal_flush(hand_cards, hole)
        if rf_result:
            cards, ace_low = rf_result
            best_hand = ["Royal Flush", cards]
            hand_score = self.get_hand_score("Royal Flush", cards, hand_cards)
            return best_hand, hand_score


        sf, ace_low = self.straight_flush(hand_cards, hole)
        if sf:
            best_hand = ["Straight Flush", sf]
            hand_score = self.get_hand_score("Straight Flush", sf,hand_cards,  ace_low)
            return best_hand, hand_score

        fk = self.four_of_kind(hand_cards, hole)
        if fk:
            best_hand = ["Four of a Kind", fk]
            hand_score = self.get_hand_score("Four of a Kind", fk, hand_cards)
            return best_hand, hand_score
        fh = self.full_house(hand_cards, hole)
        if fh:
            best_hand = ["Full House", fh]
            hand_score = self.get_hand_score("Full House", fh, hand_cards)
            return best_hand, hand_score

        fl = self.flush(hand_cards, hole)
        if fl:
            best_hand = ["Flush", fl]
            hand_score = self.get_hand_score("Flush", fl,hand_cards)
            return best_hand, hand_score


        st, ace_low = self.straight(hand_cards, hole)
        if st:
            best_hand = ["Straight", st]
            hand_score = self.get_hand_score("Straight", st, hand_cards, ace_low)
            return best_hand, hand_score

        tk = self.three_of_kind(hand_cards, hole)
        if tk:
            best_hand = ["Three of a Kind", tk]
            hand_score = self.get_hand_score("Three of a Kind", tk, hand_cards)
            return best_hand, hand_score

        tp = self.two_pair(hand_cards, hole)
        if tp:
            best_hand = ["Two Pair", tp]
            hand_score = self.get_hand_score("Two Pair", tp, hand_cards)
            return best_hand, hand_score

        op = self.one_pair(hand_cards, hole)
        if op:
            best_hand = ["One Pair", op]
            hand_score = self.get_hand_score("One Pair", op, hand_cards)
            return best_hand, hand_score

        hc  = self.high_card(hand_cards, hole)
        best_hand = ["High Card", hc]
        hand_score = self.get_hand_score("High Card", hc, hand_cards)

        return best_hand, hand_score

    def detect_ace_low_in_straight(self, cards):
        """
        Given a list of 5 cards
        determine whether the Ace is acting as low (value 1) in the straight.

        Returns:
            ace_type (int): 1 if Ace is low, else 14
        """
        ranks = [card[:-1] for card in cards]  # extract ranks (e.g. 'A', '2', '3', ...)
        ranks = tuple(ranks)
        required_low_straight = {'A', '2', '3', '4', '5'}

        # If the cards contain the low straight set, Ace is low
        if required_low_straight.issubset(set(ranks)):
            ace_low = True
            return ace_low
        else:
            ace_low = False
            return ace_low

    def royal_flush(self, hand_cards, hole):
        """ WORKS
    Check for Straight Flush involving at least 2 hole cards.
    Returns list of 5 cards forming straight flush or None.
    """



    # Group cards by suit
        suits = defaultdict(list)
        for card in hand_cards:
            rank = card[:-1]  # e.g. '10', 'J', 'Q'
            suit = card[-1]   # e.g. 'H', 'D'
            suits[suit].append(rank)

        # we are looking for 5 of these royal ranks of the same suit
        royal_ranks = {'10', 'J', 'Q', 'K', 'A'}

        for suit, ranks in suits.items():
            if royal_ranks.issubset(set(ranks)):
                # Check how many of the royal flush cards are in player's hole
                required_royals = [r + suit for r in royal_ranks]
                ace_high = True
                return required_royals, ace_high
                '''
                if self.count_hole_cards(required_royals, hole) >= 2:
                    ace_high = True
                    return required_royals, ace_high
                '''
        return None




    def straight_flush(self, hand_cards, hole):
        """ WORKS
        Check for Straight Flush involving at least 2 hole cards.
        Returns list of 5 cards forming straight flush or None.
        """

        # Group ranks by suit
        suits = defaultdict(list)
        #map face card to values
        face_card_map = {'J':11, 'Q':12, 'K':13, 'A':14}
        for card in hand_cards:
            rank = card[:-1]
            suit = card[-1]
            rank_value = face_card_map.get(rank, None)
            if rank_value is None:
                rank_value = int(rank)
            suits[suit].append(rank_value)

        # Check each suit
        for suit, ranks in suits.items():
            if len(ranks) < 5:
                continue

            unique_sorted = sorted(set(ranks))
            if 14 in unique_sorted:
                # Add 1 to represent Ace as low only if not already present
                if 1 not in unique_sorted:
                    unique_sorted = unique_sorted + [1]
                unique_sorted = sorted(unique_sorted)

            # Sliding window
            for i in range(len(unique_sorted) - 4):
                window = unique_sorted[i:i + 5]
                if all(window[j] + 1 == window[j + 1] for j in range(4)):
                    # Build cards from window
                    cards = []
                    for r in window:
                        # Convert ranks back to card strings
                        rank_str = None
                        if r == 1 or r == 14:
                            rank_str = 'A'
                        elif r == 11:
                            rank_str = 'J'
                        elif r == 12:
                            rank_str = 'Q'
                        elif r == 13:
                            rank_str = 'K'
                        else:
                            rank_str = str(r)
                        cards.append(rank_str + suit)
                    ace_low = self.detect_ace_low_in_straight(cards)
                    return cards, ace_low

                    '''
                    if self.count_hole_cards(cards, hole) >= 2:
                        ace_low = self.detect_ace_low_in_straight(cards)
                        return cards, ace_low
                    '''

        return None, None

    def four_of_kind(self, hand_cards, hole):
        """WORKS BUT ONLY RETURNS THE 4 CARDS
               Check for Four of a Kind with at least 2 hole cards.
               Returns list of 4 cards or None.
               """
        rank_groups = self.get_rank_groups(hand_cards)


        '''
        for rank, cards in rank_groups.items():
            if len(cards) == 4 and self.count_hole_cards(cards, hole) >= 2:
                return cards
        return None
        '''


        for rank, cards in rank_groups.items():
            if len(cards) == 4:
                return cards
        return None


    def full_house(self, hand_cards, hole):
        """ WORKS RETURNS THE 5 CARDS
        Check for Full House (3 + 2 cards) with at least 2 hole cards.
        Returns list of 5 cards or None.
        """

        rank_groups = self.get_rank_groups(hand_cards)
        triplets = [(rank, cards[:3]) for rank, cards in rank_groups.items() if len(cards) >= 3]
        pairs = [(rank, cards[:2]) for rank, cards in rank_groups.items() if len(cards) >= 2]

        #check to make sure they are not the same rank and check if their are hole cards
        for triplet_rank, triplet in triplets:
            for pair_rank, pair in pairs:
                if pair_rank != triplet_rank:
                    full_house_cards = triplet + pair
                    return full_house_cards


                    '''
                    if self.count_hole_cards(full_house_cards, hole) >= 2:
                        return full_house_cards
                    '''
        return None






    def flush(self, hand_cards,hole):
        """ WORKS RETURNS THE 5 CARDS
            Check for Flush (5+ cards same suit) with at least 2 hole cards.
            Returns list of suited cards or None.
            """
        suits = defaultdict(list)

        # Group cards by suit, keeping original card strings
        for card in hand_cards:
            suit = card[-1]
            suits[suit].append(card)

        for suited_cards in suits.values():
            if len(suited_cards) >= 5:
                return suited_cards
                # Count how many of these flush cards are in player's hole cards
                '''
                if self.count_hole_cards(suited_cards, hole) >= 2:
                    return suited_cards
                '''

        return None

    def straight(self, hand_cards, hole):
        """WORKS
           Check for Straight (5 consecutive ranks) with at least 2 hole cards.
           Returns list of cards forming straight or None.
           """
        # five consecutive cards of different suits
        nums = []
        rank_to_cards = defaultdict(list)
        face_card_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        for card in hand_cards:
            rank = card[:-1]
            num = face_card_map.get(rank, None)
            if num is None:
                num = int(rank)
            nums.append(num)
            rank_to_cards[num].append(card)
            if num == 14:
                rank_to_cards[1].append(card)

        unique_sorted = sorted(set(nums + [1] if 14 in nums else set(nums)))


        #use sliding window to find 5 consecutive numbers
        for i in range(len(unique_sorted) - 4):
            window = unique_sorted[i:i + 5]
            if all(window[j] + 1 == window[j + 1] for j in range(4)):
                # Found a flush — now confirm hole cards
                possible_straight = []
                used_ranks = set()

                for r in window:
                    for card in rank_to_cards[r]:
                        # Only take one card per rank to avoid duplicates
                        if r not in used_ranks:
                            possible_straight.append(card)
                            used_ranks.add(r)
                            break

                ace_low = self.detect_ace_low_in_straight(possible_straight)
                return possible_straight, ace_low

                '''
                # Check if at least 2 of them are from self.hole
                if self.count_hole_cards(possible_straight, hole) >= 2:
                    ace_low = self.detect_ace_low_in_straight(possible_straight)
                    return possible_straight, ace_low
                '''

        return None, None


    def three_of_kind(self, hand_cards, hole):
        """ WORKS RETURNS THE 3 CARDS OF THE THREE OF KIND
               Check for Three of a Kind with at least 2 hole cards.
               Returns list of 3 cards or None.
               """
        rank_groups = self.get_rank_groups(hand_cards)
        for cards in rank_groups.values():
            if len(cards) == 3:
                return cards

            '''
            if len(cards) == 3 and self.count_hole_cards(cards, hole) >= 2:
                return cards
            '''
        return None

    def two_pair(self, hand_cards, hole):
        """WORKS RETURNS 4 CARDS THE 2 PAIRS
                Check for Two Pair with at least 2 hole cards.
                Returns list of 4 cards or None.
                """

        rank_groups = self.get_rank_groups(hand_cards)
        pairs = [cards[:2] for cards in rank_groups.values() if len(cards) >= 2]
        if len(pairs) >= 2:
            combined = pairs[0] + pairs[1]
            return combined
            '''
            if self.count_hole_cards(combined, hole) >= 2:
                return combined
            '''
        return None




    def one_pair(self, hand_cards, hole):
        """WORKS AND RETURNS THE 2 CARDS THAT MAKE UP THE PAIR
               Check for One Pair with at least 2 hole cards.
               Returns list of 2 cards or None.
               """
        rank_groups = self.get_rank_groups(hand_cards)
        for cards in rank_groups.values():
            if len(cards) == 2:
                return cards
            '''
            if len(cards) == 2 and self.count_hole_cards(cards, hole) >= 2:
                return cards
            '''
        return None

    def high_card(self, hand_cards, hole):
        """ WORKS RETURNS A TUPLE WITH THE BEST COMBO AND THEIR CORRESPONDING RANKS
                Find best 5-card combo with exactly 2 hole cards.
                Returns tuple (combo, sorted ranks).
                """
        #print(f"Called high_card with hand_cards: {hand_cards}, hole: {hole}")
        valid_combos = []
        for combo in combinations(hand_cards, 5):
            hole_count = sum(1 for card in combo if card in hole)

            if hole_count == 2:
                valid_combos.append(combo)
        best_combo = None
        best_ranks = []
        for combo in valid_combos:
            ranks = sorted([self.rank_value(card) for card in combo], reverse=True)
            if not best_combo or ranks > best_ranks:
                best_combo = combo
                best_ranks = ranks

        return list(best_combo) if best_combo else None

    def rank_value(self, card):
        """Convert card rank to numerical value for comparison."""
        rank = card[:-1]
        mapping = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        if rank in mapping:
            return mapping[rank]
        else:
            return int(rank)



    def get_hand_score(self, hand_type, cards, hand_cards, ace_low= False):
        ace_type = 1 if ace_low else 14
        if hand_type in ['Straight Flush', 'Straight']:
            face_card_map = {'J': 11, 'Q': 12, 'K': 13, 'A': ace_type}  # Ace low or high depending on ace_type
        else:
            face_card_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}

        def safe_rank(rank):
            """Convert rank string to int, fallback to 0 if something goes wrong"""
            if rank in face_card_map:
                return face_card_map[rank]
            try:
                return int(rank)
            except:
                return 0

        score_rank = []
        hand_score = self.HAND_RANKS.get(hand_type,0)
        score_rank.append(hand_score)

        if hand_type == 'Royal Flush':
            '''
            This works no issue here
            '''
            return score_rank

        if hand_type in ['Straight Flush', 'Straight']:
            nums = [safe_rank(c[:-1]) for c in cards]
            nums.sort(reverse=True)
            score_rank.append(nums[0])
            return score_rank

        if hand_type == 'Four of a Kind':
            score_rank.append(safe_rank(cards[0][:-1]))
            additional_cards = [safe_rank(c[:-1]) for c in hand_cards if c not in cards]
            additional_cards.sort(reverse=True)
            score_rank.append(additional_cards[0] if additional_cards else 0)
            return score_rank

        if hand_type == 'Full House':
            rank_counts = {}
            for card in cards:
                r = safe_rank(card[:-1])
                rank_counts[r] = rank_counts.get(r, 0) + 1
            three_rank = max([r for r, count in rank_counts.items() if count == 3], default=0)
            pair_rank = max([r for r, count in rank_counts.items() if count == 2], default=0)
            score_rank.append(three_rank)
            score_rank.append(pair_rank)
            return score_rank

        if hand_type == 'Flush':
            nums = [safe_rank(c[:-1]) for c in cards]
            nums.sort(reverse=True)
            score_rank.extend(nums)
            return score_rank

        if hand_type == 'Three of a Kind':
            score_rank.append(safe_rank(cards[0][:-1]))
            additional_cards = [safe_rank(c[:-1]) for c in hand_cards if c not in cards]
            additional_cards.sort(reverse=True)
            score_rank.append(additional_cards[0] if len(additional_cards) > 0 else 0)
            score_rank.append(additional_cards[1] if len(additional_cards) > 1 else 0)
            return score_rank

        if hand_type == 'Two Pair':
            ranks = sorted(list({safe_rank(c[:-1]) for c in cards}), reverse=True)
            temp_list = [safe_rank(c[:-1]) for c in hand_cards if c not in cards]
            temp_list.sort(reverse=True)
            ranks.append(temp_list[0] if temp_list else 0)
            score_rank.extend(ranks)
            return score_rank

        if hand_type == 'One Pair':
            score_rank.append(safe_rank(cards[0][:-1]))
            temp_list = [safe_rank(c[:-1]) for c in hand_cards if c not in cards]
            temp_list.sort(reverse=True)
            # Pad to always have 3 kickers
            temp_list += [0] * (3 - len(temp_list))
            score_rank.extend(temp_list[:3])
            return score_rank

        if hand_type == 'High Card':
            nums = [safe_rank(c[:-1]) for c in cards]
            nums.sort(reverse=True)
            # Pad to always have 5 cards
            nums += [0] * (5 - len(nums))
            score_rank.extend(nums[:5])
            return score_rank

        return score_rank
