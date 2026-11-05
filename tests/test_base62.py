from app.base62 import ALPHABET, decode, encode, random_code


def test_encode_decode_round_trip():
    for n in [0, 1, 61, 62, 123456789, 62**7 - 1]:
        assert decode(encode(n)) == n


def test_random_code_is_7_chars_from_alphabet():
    for _ in range(1000):
        code = random_code()
        assert len(code) == 7
        assert all(ch in ALPHABET for ch in code)