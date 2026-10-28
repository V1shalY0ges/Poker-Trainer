# COMMENTS ARE DONE HERE

# defaultdict is used to group cards by rank or suit automatically
from collections import defaultdict

# combinations is used to generate all 5-card hand combinations
from itertools import combinations

import random
#each poker hand is unique so it needs its own method


# ------------- HandEvaluator Class ------------------
# This class is responsible for:
# - Determining the best poker hand a player can make
# - Ranking hands correctly
# - Generating a numerical score for comparing hands


class HandEvaluator():
    # Dictionary mapping each hand type to a numerical strength value
    # Higher number = stronger hand, this is the first value in the list of scores

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

    # Groups cards by rank (e.g. all Kings together)
    def get_rank_groups(self, cards):
        rank_groups = defaultdict(list)

        # Extract the rank
        for card in cards:
            rank = card[:-1]
            rank_groups[rank].append(card)
        return rank_groups

    # Main hand evaluation method
    # Determines the strongest possible hand in correct priority order
    # Try each hand check; if it returns cards (not None), return the hand name and cards
    def evaluate_hand(self, player, community_cards):

        """
        Evaluates a player's best possible hand using their hole cards
        and the community cards.
        """

        # Player's private game cards
        hole = player.hole_cards
        print(f"HOLE FOR EVALUATE HAND: {hole}")

        # Combine them with the board cards to get the full 7 cards
        hand_cards = player.hole_cards + community_cards
        print(hand_cards)
        '''
        if len(hand_cards) < 7:
            needed = 7 - len(hand_cards)
            all_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
            all_suits = ['H', 'D', 'C', 'S']

            # generate random unique cards not already in hand_cards
            generated = []
            while len(generated) < needed:
                card = random.choice(all_ranks) + random.choice(all_suits)
                if card not in hand_cards and card not in generated:
                    generated.append(card)
            hand_cards += generated
        '''
        ace_low = False

        # ---------- Royal Flush ----------
        rf_result= self.royal_flush(hand_cards, hole)
        if rf_result: # If we don't have a royal flush we go down and check the next layer
            cards, ace_low = rf_result
            player.best_hand = ["Royal Flush", cards]

            # The method to generate the hand score for the cards that make the kicker and draws
            player.hand_score = self.get_hand_score("Royal Flush", cards, hand_cards)
            return player.best_hand, player.hand_score

        # ---------- Straight Flush ----------
        sf, ace_low = self.straight_flush(hand_cards, hole)
        if sf:
            player.best_hand = ["Straight Flush", sf]
            player.hand_score = self.get_hand_score("Straight Flush", sf,hand_cards,  ace_low)
            return player.best_hand, player.hand_score

        # ---------- Four of a Kind ----------
        fk = self.four_of_kind(hand_cards, hole)
        if fk:
            player.best_hand = ["Four of a Kind", fk]
            player.hand_score = self.get_hand_score("Four of a Kind", fk, hand_cards)
            return player.best_hand, player.hand_score

        # ---------- Full House ----------
        fh = self.full_house(hand_cards, hole)
        if fh:
            player.best_hand = ["Full House", fh]
            player.hand_score = self.get_hand_score("Full House", fh, hand_cards)
            return player.best_hand, player.hand_score

        # ---------- Flush ----------
        fl = self.flush(hand_cards, hole)
        if fl:
            player.best_hand = ["Flush", fl]
            player.hand_score = self.get_hand_score("Flush", fl,hand_cards)
            return player.best_hand, player.hand_score

        # ---------- Straight ----------
        st, ace_low = self.straight(hand_cards, hole)
        if st:
            player.best_hand = ["Straight", st]
            player.hand_score = self.get_hand_score("Straight", st, hand_cards, ace_low)
            return player.best_hand, player.hand_score

        # ---------- Three of Kind ----------
        tk = self.three_of_kind(hand_cards, hole)
        if tk:
            player.best_hand = ["Three of a Kind", tk]
            player.hand_score = self.get_hand_score("Three of a Kind", tk, hand_cards)
            return player.best_hand, player.hand_score

        # ---------- Two Pair ----------
        tp = self.two_pair(hand_cards, hole)
        if tp:
            player.best_hand = ["Two Pair", tp]
            player.hand_score = self.get_hand_score("Two Pair", tp, hand_cards)
            return player.best_hand, player.hand_score

        # ---------- One Pair ----------
        op = self.one_pair(hand_cards, hole)
        if op:
            player.best_hand = ["One Pair", op]
            player.hand_score = self.get_hand_score("One Pair", op, hand_cards)
            return player.best_hand, player.hand_score

        # ---------- High Card ----------
        hc  = self.high_card(hand_cards, hole)
        player.best_hand = ["High Card", hc]
        player.hand_score = self.get_hand_score("High Card", hc, hand_cards)

        return player.best_hand, player.hand_score

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
        """
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
                # Check how many of the royal flush cards are in player's hole through direct comparison

                # By building the exact card strings
                required_royals = [r + suit for r in royal_ranks]
                ace_high = True
                return required_royals, ace_high

        return None




    def straight_flush(self, hand_cards, hole):
        """
        Check for Straight Flush involving at least 2 hole cards.
        Returns list of 5 cards forming straight flush or None.
        """

        # Group ranks by suit
        suits = defaultdict(list)
        #map face card to values
        face_card_map = {'J':11, 'Q':12, 'K':13, 'A':14}
        for card in hand_cards:
            # Extract the rank and cards
            rank = card[:-1]
            suit = card[-1]

            # Working with integers so we want to convert royals and aces into numerical representation
            rank_value = face_card_map.get(rank, None)
            if rank_value is None:
                rank_value = int(rank)
            suits[suit].append(rank_value)

        # Check each suit
        for suit, ranks in suits.items():
            if len(ranks) < 5:
                continue # Dont have the 5 cards of one suit to make a straight

            unique_sorted = sorted(set(ranks))
            if 14 in unique_sorted:
                # Add 1 to represent Ace as low only if not already present
                if 1 not in unique_sorted:
                    unique_sorted = unique_sorted + [1]
                unique_sorted = sorted(unique_sorted) # Sort it to go through it using sliding window

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

                    # Check if the ace used is a low or high
                    ace_low = self.detect_ace_low_in_straight(cards)
                    return cards, ace_low

                    '''
                    if self.count_hole_cards(cards, hole) >= 2:
                        ace_low = self.detect_ace_low_in_straight(cards)
                        return cards, ace_low
                    '''

        return None, None

    def four_of_kind(self, hand_cards, hole):
        """
        check for Four of a Kind
        Returns list of 4 cards or None.
        """

        # Convert the cards into a dictionary of rank groups
        rank_groups = self.get_rank_groups(hand_cards)


        '''
        for rank, cards in rank_groups.items():
            if len(cards) == 4 and self.count_hole_cards(cards, hole) >= 2:
                return cards
        return None
        '''


        for rank, cards in rank_groups.items():
            # Goes through each rank and look at the values/ suits and we need 4 of them to make a 4 of kind
            if len(cards) == 4:
                return cards
        return None


    def full_house(self, hand_cards, hole):
        """
        Check for Full House
        Returns list of 5 cards or None.
        """
        # Convert the cards into the dictionary for easy lookup
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
        """
               Check for Three of a Kind

               """
        # Same logic as 4 of kind but this times only checks if we have 3 of the same rank
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
        """
        Check for Two Pair
        """
        # Generate the dictionary of ranks and the suits for it
        rank_groups = self.get_rank_groups(hand_cards)

        # Go thorugh each pair and check if we can make a pair as the cards to make a pair need to be greater than 2
        pairs = [cards[:2] for cards in rank_groups.values() if len(cards) >= 2]

        # Check if the length of the pairs list is greater than 2 as we have 2 cards for the pair
        if len(pairs) >= 2:

            # Make the full pair and return it
            combined = pairs[0] + pairs[1]
            return combined
            '''
            if self.count_hole_cards(combined, hole) >= 2:
                return combined
            '''
        return None




    def one_pair(self, hand_cards, hole):
        """
        Check for One Pair
        """

        # Follows same logic as 4 of kind and 3 of kind but only looking for 2 of same rank
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
        """
        Find best 5-card combo
        Returns tuple (combo, sorted ranks).
        """
        # Debugging check
        print(f"Called high_card with hand_cards: {hand_cards}, hole: {hole}")

        # Generate all the valid 5 card combinations from the 7 cards
        valid_combos = []
        for combo in combinations(hand_cards, 5):
            hole_count = sum(1 for card in combo if card in hole)

            if hole_count == 2:
                valid_combos.append(combo)
        best_combo = None
        best_ranks = []
        for combo in valid_combos:
            # Sort by the best ranks of each combo
            ranks = sorted([self.rank_value(card) for card in combo], reverse=True)

            # Compare it to the one we have stored and replace if better
            if not best_combo or ranks > best_ranks:
                best_combo = combo
                best_ranks = ranks

        return list(best_combo) if best_combo else None

    def rank_value(self, card):
        """Convert card rank to numerical value for comparison."""

        # Extract the rank portion
        rank = card[:-1]

        # Make it all numerical using hashmap
        mapping = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        if rank in mapping:
            return mapping[rank]
        else:
            return int(rank)

    # --------------------------------------------------
    # Generates a numerical score used to compare hands
    def get_hand_score(self, hand_type, cards, hand_cards, ace_low= False):

        """
        Produces a list representing hand strength and tie-breakers.
        """

        # Use the ace_low flag from the best 5 cards to be consistent with the score
        ace_type = 1 if ace_low else 14
        if hand_type in ['Straight Flush', 'Straight']:
            face_card_map = {'J': 11, 'Q': 12, 'K': 13, 'A': ace_type}  # Ace low or high depending on ace_type
        else:
            face_card_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        score_rank = []
        hand_score = self.HAND_RANKS.get(hand_type,0) # Get the initial primary value based on the actual hand type
        score_rank.append(hand_score)

        if hand_type == 'Royal Flush':
            '''
            This works nothing needed because no kicker or draw cards as royal flush unique
            '''
            return score_rank

        if hand_type in ['Straight Flush', 'Straight']:
            '''
            no kicker here and tiebreaker determined by highest card
            '''
            nums = []
            # Iterate through the 5 cards
            for card in cards:

                # Extract the rank
                rank = card[:-1]

                # Extract the numerical representation
                rank_value = face_card_map.get(rank)
                if rank_value is None:
                    rank_value = int(rank)
                # Add it to the temporary nums list
                nums.append(rank_value)
            # Sort to the have the highest rank number 1st
            nums.sort(reverse=True)

            # Append the highest number to the score rank and that is all that is returned
            score_rank.append(nums[0])
            return score_rank

        if hand_type == 'Four of a Kind':
            #we are passing in the 4 cards already
            # All have the same rank so we add it into the score rank
            card_temp = cards[0]
            rank = card_temp[:-1]
            rank_value = face_card_map.get(rank, None)
            score_rank.append(rank_value)

            # Same process as most of the remaining cards
            # Iterate through rest, get the numerical rank
            # Add it to the temporary list, sort it and then add it to the score rank
            additional_cards = []
            for card in hand_cards:
                if card not in cards:
                    rank = card[:-1]
                    rank_value = face_card_map.get(rank, None)
                    if rank_value is None:
                        rank_value = int(rank)
                    additional_cards.append(rank_value)
            additional_cards.sort(reverse=True)
            score_rank.append(additional_cards[0])

            return score_rank

        if hand_type == 'Full House':
            rank_counts = {}
            for card in cards:
                rank = card[:-1]
                rank_value = face_card_map.get(rank, None)
                if rank_value is None:
                    rank_value = int(rank)
                rank_counts[rank_value] = rank_counts.get(rank_value, 0) + 1

            # Find three of a kind rank
            three_rank = max([rank for rank, count in rank_counts.items() if count == 3])
            # Find pair rank
            pair_rank = max([rank for rank, count in rank_counts.items() if count == 2])

            score_rank.append(three_rank)
            score_rank.append(pair_rank)
            return score_rank

        if hand_type == 'Flush':
            # For flush, add all 5 cards sorted high to low for tie-break
            # Same process as most of the remaining cards
            # Iterate through rest, get the numerical rank
            # Add it to the temporary list, sort it and then add it to the score rank
            nums = []
            for card in cards:
                rank = card[:-1]
                rank_value = face_card_map.get(rank)
                if rank_value is None:
                    rank_value = int(rank)
                nums.append(rank_value)
            nums.sort(reverse=True)

            score_rank.extend(nums)
            return score_rank

        if hand_type == 'Three of a Kind':
            # we are passing in the 3 cards already so they should all have the same rank
            # All have the same rank so we add it into the score rank

            card_temp = cards[0]
            rank = card_temp[:-1]
            rank_value = face_card_map.get(rank, None)
            score_rank.append(rank_value)

            # Same process as most of the remaining cards
            # Iterate through rest, get the numerical rank
            # Add it to the temporary list, sort it and then add it to the score rank
            additional_cards = []
            for card in hand_cards:
                if card not in cards:
                    rank = card[:-1]

                    rank_value = face_card_map.get(rank, None)
                    if rank_value is None:
                        rank_value = int(rank)

                    additional_cards.append(rank_value)
            additional_cards.sort(reverse=True)
            score_rank.append(additional_cards[0])
            score_rank.append(additional_cards[1])

            return score_rank

        if hand_type == 'Two Pair':
            #we are passing in the 2 pairs (4 cards) already we just need to detemine them
            ranks = []
            temp_list = []
            # We are getting the ranks for the 2 cards in the 2 pair making it numerical and then adding it to the ranks list
            # We sort it and extend it into the actual score lis t
            for card in cards:
                rank = card[:-1]
                rank_value = face_card_map.get(rank, None)
                # This is more actual number cards so '9H' we need to convert the string 9 to integer 9
                if rank_value is None:
                    rank_value = int(rank)
                if rank_value not in ranks:
                    ranks.append(rank_value)
            ranks.sort(reverse=True)

            # Same sorting logic for the rest of the remaining cards
            # Get numerical value and then sort and add into the score rank list
            for card in hand_cards:
                if card not in cards:
                    rank = card[:-1]
                    rank_value = face_card_map.get(rank, None)
                    if rank_value is None:
                        rank_value = int(rank)
                    temp_list.append(rank_value)
            temp_list.sort(reverse=True)
            ranks.append(temp_list[0])
            score_rank.extend(ranks)
            return score_rank


        if hand_type == 'One Pair':
            # Cards is the 2 cards that make up the one pair
            # They both have the same rank so we just need to get one card from cards
            card = cards[0]
            rank = card[:-1]
            temp_list = []
            rank_value = face_card_map.get(rank, None)
            if rank_value is None:
                rank_value = int(rank)
            # We add the rank value that is the same for both cards
            score_rank.append(rank_value)

            # Next the rest is the numerical value sorted of the rest of the cards
            # Follows same logic that most of them do
            for card in hand_cards:
                if card not in cards:
                    rank = card[:-1]
                    rank_value = face_card_map.get(rank, None)
                    if rank_value is None:
                        rank_value = int(rank)
                    temp_list.append(rank_value)
            temp_list.sort(reverse=True)
            score_rank.extend(temp_list)

            return score_rank

        if hand_type == 'High Card':
            # We are just ordering the 5 cards based on numerical value and returning it
            nums = []
            # Iterate through the cards
            for card in cards:

                # Extract the rank and numerical value for it
                rank = card[:-1]
                rank_value = face_card_map.get(rank, None)

                if rank_value is None:
                    rank_value = int(rank)
                nums.append(rank_value)

            # Sort the numbers
            nums.sort(reverse=True)
            # Add top 5 cards for tie-breaks
            score_rank.extend(nums)
            return score_rank
