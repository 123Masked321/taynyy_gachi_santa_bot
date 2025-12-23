import random
from typing import List, Dict


def shuffle_list(players:  List[int]) -> List[tuple[int, int]]:
    if len(players) < 3:
        raise ValueError('Минимум 3 надо')

    random.shuffle(players)

    return [(players[i], players[(i + 1) % len(players)]) for i in range(len(players))]