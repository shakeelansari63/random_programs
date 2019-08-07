from datetime import datetime
from hashlib import sha512
import re
import itertools as it

def shuffle_cards(deck):
    seed = datetime.strftime(datetime.today(), '%Y%m%d%H%M%S%f')
    hash_seed = sha512(seed.encode('ascii')).hexdigest()
    number_str = "".join(re.compile(r'[0-9]').findall(hash_seed))
    new_pos = []
    i = 0
    while i < len(number_str) - 2 and len(new_pos) < 52:
        j = i + 1
        num_digit = int(number_str[i] + number_str[j])
        if num_digit > 51: num_digit %= 52
        new_pos.append(num_digit)
        i = j
    i = 0
    while i < len(number_str) - 3  and len(new_pos) < 52:
        j = i + 2
        num_digit = int(number_str[i] + number_str[j])
        if num_digit > 51: num_digit %= 52
        new_pos.append(num_digit)
        i = j - 1
    for old_pos, new_pos in enumerate(new_pos):
        card = deck.pop(old_pos)
        deck.insert(new_pos, card)


deck = ['AceOfHeart', '2OfHeart', '3OfHeart', '4OfHeart', '5OfHeart',
         '6OfHeart', '7OfHeart', '8OfHeart', '9OfHeart', '10OfHeart',
         'JackOfHeart', 'QueenOfHeart', 'KingOfHeart',
         'AceOfDiamond', '2OfDiamond', '3OfDiamond', '4OfDiamond', '5OfDiamond',
         '6OfDiamond', '7OfDiamond', '8OfDiamond', '9OfDiamond', '10OfDiamond',
         'JackOfDiamond', 'QueenOfDiamond', 'KingOfDiamond',
         'AceOfSpade', '2OfSpade', '3OfSpade', '4OfSpade', '5OfSpade',
         '6OfSpade', '7OfSpade', '8OfSpade', '9OfSpade', '10OfSpade',
         'JackOfSpade', 'QueenOfSpade', 'KingOfSpade',
         'AceOfClub', '2OfClub', '3OfClub', '4OfClub', '5OfClub',
         '6OfClub', '7OfClub', '8OfClub', '9OfClub', '10OfClub',
         'JackOfClub', 'QueenOfClub', 'KingOfClub'
]

shuffle_cards(deck)
print(deck)
