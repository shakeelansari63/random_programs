from datetime import datetime
from hashlib import sha512
import re
import itertools as it

def shuffle_cards(deck):
    # Generate a string for hashing.
    # Here we use Current Timestamp which will always be different everytime we run the program
    seed = datetime.strftime(datetime.today(), '%Y%m%d%H%M%S%f')
    
    # Calculate Hash of the Seed Value.
    # This will generate a hexadecimal hash value of seed
    hash_seed = sha512(seed.encode('ascii')).hexdigest()
    
    # Now extract numbers from hash string
    number_str = "".join(re.compile(r'[0-9]').findall(hash_seed))
    
    # Now create a new empty list. This list will be populated with random 52 numbers to shuffle card
    new_pos = []
    
    # Now we extract set of 2 adjacent numbers from the string till we either reach end of string or have 52 values in list
    i = 0
    while i < len(number_str) - 1 and len(new_pos) < 52:
        j = i + 1
        num_digit = int(number_str[i] + number_str[j])
        # if a number is larger than 51, we take modulus of that number to bring it between 0 - 51
        if num_digit > 51: num_digit %= 52
        new_pos.append(num_digit)
        i = j
    
    # This is a safe play. If we don't get 52 number from above loop, we try to fill it with alternate number set in this step
    i = 0
    while i < len(number_str) - 2 and len(new_pos) < 52:
        j = i + 2
        num_digit = int(number_str[i] + number_str[j])
        # if a number is larger than 51, we take modulus of that number to bring it between 0 - 51
        if num_digit > 51: num_digit %= 52
        new_pos.append(num_digit)
        i = j - 1
    
    # By now we should have 52 numbers in out list. so we start shuffling
    # We take the index of number in list as old position and number itself as new position
    for old_pos, new_pos in enumerate(new_pos):
        # Pop out card from deck
        card = deck.pop(old_pos)
        
        # Put the card in new position
        deck.insert(new_pos, card)

if __name__ == '__main__':
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
         'JackOfClub', 'QueenOfClub', 'KingOfClub']

    shuffle_cards(deck)
    print(deck)
