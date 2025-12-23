import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits


def generate_game_code(code_len=8) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(code_len))
