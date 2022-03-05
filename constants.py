SLOT_HEAD = 0
SLOT_NECK = 1
SLOT_SHOULDERS = 2
SLOT_SHIRT = 3
SLOT_CHEST = 4
SLOT_BELT = 5
SLOT_LEGS = 6
SLOT_FEET = 7
SLOT_WRISTS = 8
SLOT_HANDS = 9
SLOT_FINGER1 = 10
SLOT_FINGER2 = 11
SLOT_TRINKET1 = 12
SLOT_TRINKET2 = 13
SLOT_BACK = 14
SLOT_MAIN_HAND = 15
SLOT_OFF_HAND = 16
SLOT_RANGED = 17
SLOT_TABARD = 18

UNENCHANTABLE_SLOTS = [SLOT_NECK, SLOT_SHIRT, SLOT_BELT, SLOT_FINGER1, SLOT_FINGER2, SLOT_TRINKET1, SLOT_TRINKET2,
                       SLOT_RANGED, SLOT_TABARD]

HIGH_RESIST = {
    120: 37,
    117: 36,
    114: 35,
    111: 34,
    109: 39,    # rare
    108: 33,
    105: 32,
    102: 31,
    99: 30,
    96: 29,
    93: 28,
    90: 27,
    87: 26,
    84: 25,
    82: 31,     # rare
    81: 24,
}

MED_RESIST = {
    120: 27,
    117: 27,
    114: 26,
    111: 25,
    109: 30,    # rare
    108: 25,
    105: 23,
    102: 23,
    99: 22,
    96: 21,
    93: 21,
    91: 26,     # rare
    90: 20,
    87: 19,
    84: 19,
    81: 17,
}

LOW_RESIST = {
    120: 21,
    117: 20,
    115: 27,    # epic
    114: 19,
    111: 19,
    108: 18,
    105: 17,
    103: 21,    # rare
    102: 17,
    99: 17,
    96: 16,
    94: 19,     # rare
    93: 15,
    90: 15,
    87: 14,
    84: 13,
    81: 13,
}

RESIST_RANDOM_ENCHANT_BY_SLOT = {
    0: HIGH_RESIST,
    1: LOW_RESIST,
    2: MED_RESIST,
    4: HIGH_RESIST,
    5: MED_RESIST,
    6: HIGH_RESIST,
    7: MED_RESIST,
    8: LOW_RESIST,
    9: MED_RESIST,
    10: LOW_RESIST,
    11: LOW_RESIST,
    14: LOW_RESIST,
    16: LOW_RESIST,
}

RESISTANCE_GEMS = {
    22459: {
        'arcane': 4,
        'fire': 4,
        'frost': 4,
        'nature': 4,
        'shadow': 4,
    },
    22460: {
        'arcane': 3,
        'fire': 3,
        'frost': 3,
        'nature': 3,
        'shadow': 3,
    }
}

RESISTANCE_ENCHANTS = {
    1441: {  # Enchant Cloak - Greater Shadow Resistance
        'shadow': 15
    },
    1257: {  # Enchant Cloak - Greater Arcane Resistance
        'arcane': 15
    },
    2664: {  # Enchant Cloak - Major Resistance
        'arcane': 7,
        'fire': 7,
        'frost': 7,
        'nature': 7,
        'shadow': 7
    },
    1888: {  # Enchant Shield - Resistance (Enchant Cloak - Greater Resistance)
        'arcane': 5,
        'fire': 5,
        'frost': 5,
        'nature': 5,
        'shadow': 5
    },
    2620: {  # Enchant Cloak - Greater Nature Resistance
        'nature': 15
    },
    2619: {  # Enchant Cloak - Greater Fire Resistance
        'fire': 15
    },
    926: {  # Enchant Shield - Frost Resistance
        'frost': 8
    },
    903: {  # Enchant Cloak - Resistance
        'arcane': 3,
        'fire': 3,
        'frost': 3,
        'nature': 3,
        'shadow': 3
    },
    2463: {  # Enchant Cloak - Fire Resistance
        'fire': 7
    },
    804: {  # Enchant Cloak - Lesser Shadow Resistance
        'shadow': 10
    },
    256: {  # Enchant Cloak - Lesser Fire Resistance
        'fire': 5
    },
    65: {   # Enchant Cloak - Minor Resistance
        'arcane': 1,
        'fire': 1,
        'frost': 1,
        'nature': 1,
        'shadow': 1
    },
    2984: {  # Shadow Armor Kit
        'shadow': 8
    },
    3009: {  # Glyph of Shadow Warding
        'shadow': 20
    },
    2683: {  # Shadow Guard
        'shadow': 10
    },
    2998: {  # Inscription of Endurance
        'arcane': 7,
        'fire': 7,
        'frost': 7,
        'nature': 7,
        'shadow': 7
    },
    2985: {  # Flame Armor Kit
        'fire': 8
    },
    2487: {  # Shadow Mantle of the Dawn
        'shadow': 5
    },
    1505: {  # Lesser Arcanum of Resilience
        'fire': 20
    },
    3007: {  # Glyph of Fire Warding
        'fire': 20
    },
    2988: {  # Nature Armor Kit
        'nature': 8
    },
    2987: {  # Frost Armor Kit
        'frost': 8
    },
    3008: {  # Glyph of Frost Warding
        'frost': 20
    },
    2488: {  # Chromatic Mandle of the Dawn
        'arcane': 5,
        'fire': 5,
        'frost': 5,
        'nature': 5,
        'shadow': 5
    },
    2989: {  # Arcane Armor Kit
        'arcane': 8
    },
    2681: {  # Savage Guard
        'nature': 10
    },
    3095: {  # Glyph of Chromatic Warding
        'arcane': 8,
        'fire': 8,
        'frost': 8,
        'nature': 8,
        'shadow': 8
    },
    2483: {  # Flame Mantle of the Dawn
        'fire': 5
    },
    3006: {  # Glyph of Arcane Warding
        'arcane': 20
    },
    2485: {  # Arcane Mantle of the Dawn
        'arcane': 5
    },
    2682: {  # Ice Guard
        'frost': 10
    },
    2484: {  # Frost Guard
        'frost': 5
    },
    2486: {  # Nature Mantle of the Dawn
        'nature': 5
    }
}

RESISTANCE_BUFFS = {
    976: {  # Shadow Protection (Rank 1)
        'shadow': 30
    },
    10957: {  # Shadow Protection (Rank 2)
        'shadow': 45
    },
    10958: {  # Shadow Protection (Rank 3)
        'shadow': 60
    },
    39226: {  # Prayer of Shadow Protection (Rank 1)
        'shadow': 60
    },
    25433: {  # Shadow Protection (Rank 4)
        'shadow': 70
    },
    39374: {  # Prayer of Shadow Protection (Rank 2)
        'shadow': 70
    },
    6117: {  # Mage Armor (Rank 1)
        'arcane': 5,
        'fire': 5,
        'frost': 5,
        'nature': 5,
        'shadow': 5
    },
    22782: {  # Mage Armor (Rank 2)
        'arcane': 10,
        'fire': 10,
        'frost': 10,
        'nature': 10,
        'shadow': 10
    },
    22783: {  # Mage Armor (Rank 3)
        'arcane': 15,
        'fire': 15,
        'frost': 15,
        'nature': 15,
        'shadow': 15
    },
    27125: {  # Mage Armor (Rank 4)
        'arcane': 18,
        'fire': 18,
        'frost': 18,
        'nature': 18,
        'shadow': 18
    },
    45619: {  # Broiled Bloodfin
        'arcane': 8,
        'fire': 8,
        'frost': 8,
        'nature': 8,
        'shadow': 8
    },
    42735: {  # Flask of Chromatic Wonder
        'arcane': 35,
        'fire': 35,
        'frost': 35,
        'nature': 35,
        'shadow': 35
    },
    17629: {  # Flask of Chromatic Resistance
        'arcane': 25,
        'fire': 25,
        'frost': 25,
        'nature': 25,
        'shadow': 25
    },
}
