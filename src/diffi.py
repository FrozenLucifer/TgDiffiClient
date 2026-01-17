import random
from sympy import isprime


def generate_prime_candidate(length):
    """Генерирует кандидат в простые числа заданной длины в битах."""
    p = random.getrandbits(length)
    p |= (1 << length - 1) | 1
    return p


def generate_prime(length):
    """Генерирует простое число заданной длины в битах."""
    p = 4
    while not isprime(p):
        p = generate_prime_candidate(length)
    return p


def get_generator(p):
    """Находит базу g, соответствующую простому числу p."""
    for g in range(11, p):
        if pow(g, (p - 1) // 2, p) != 1:  # Проверка на то, что g является генератором
            return g
    return None


def generate_dh_parameters(length=512):
    """Генерирует открытые параметры для Диффи-Хелмана."""
    p = generate_prime(length)
    g = get_generator(p)
    return p, g
