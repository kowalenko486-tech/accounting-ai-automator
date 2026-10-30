import re

def validate_nip_modulo11(nip: str) -> bool:
    """
    Validates Polish NIP (Tax Identification Number) using modulo-11 checksum.
    Weights: [6, 5, 7, 2, 3, 4, 5, 6, 7]
    """
    if not nip:
        return False
    clean_nip = re.sub(r'[\s\-]', '', nip)
    if len(clean_nip) != 10 or not clean_nip.isdigit():
        return False
    
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(clean_nip[i]) * weights[i] for i in range(9)) % 11
    return checksum == int(clean_nip[9])

def validate_iban_mod97(iban: str) -> bool:
    """
    Validates International Bank Account Number (IBAN) using ISO/IEC 7064 (MOD 97-10).
    """
    if not iban:
        return False
    clean_iban = re.sub(r'[\s\-]', '', iban).upper()
    if len(clean_iban) < 15 or len(clean_iban) > 34:
        return False
    
    # Move first 4 characters to the end
    rearranged = clean_iban[4:] + clean_iban[:4]
    
    # Convert letters to digits (A=10, B=11, ... Z=35)
    numeric_str = ''
    for char in rearranged:
        if char.isdigit():
            numeric_str += char
        elif char.isalpha():
            numeric_str += str(ord(char) - ord('A') + 10)
        else:
            return False
            
    # Compute modulo 97
    return int(numeric_str) % 97 == 1
