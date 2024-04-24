"""
This module contains a function to generate random text from a predefined list.
The function ensures that the same text is not repeated consecutively.
"""

import random


def generate_random_text(previous_text):
    random_texts = [
        "Haalarimerkit on niin kuin Pokemonit eiks jeh?",
        "Haalarimerkit on kuin tatuoinnit, mutta ei niin kivuliaita.",
        "Haalarimerkit muistuttavat meitä tunteista, olipa ne rakkautta, iloa tai surua",
        "Live laugh love, haalarimerkit",
        "Carpe diem",
        "#approt #apollojatkot #tunnen_kuinka_vauhti_kiihtyy",
        "Oispa risse...",
        "Bmur? Bmur!",
        "Mis jatkot?",
    ]
    random_text = random.choice(random_texts)
    while random_text == previous_text:
        random_text = random.choice(random_texts)
    return random_text
