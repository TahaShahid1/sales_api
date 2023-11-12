import string
import random

def generate_rand(type: str = 'sku', length: int = 9) -> str:
    """
    Generate random string. Can generate password/SKU
    :param type: generation type
    :return:
    """
    if type == 'sku':
        res = ''.join(random.choices(string.ascii_uppercase +
                                     string.digits, k=4))
    elif type == 'password':
        res = ''.join(random.choices(string.ascii_uppercase +
                                     string.digits, k=9))

    else:
        res = ''.join(random.choices(string.ascii_uppercase +
                                     string.digits, k=length))

    return res