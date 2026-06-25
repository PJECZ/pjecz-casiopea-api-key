"""
Safe string
"""

import re
import uuid

from unidecode import unidecode

CLAVE_REGEXP = r"^[a-zA-Z0-9-]{1,16}$"
CONCEPTO_REGEXP = r"^[PD][a-zA-Z0-9][a-zA-Z0-9]$"
CONTRASENA_REGEXP = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,48}$"
CURP_REGEXP = r"^[a-zA-Z]{4}\d{6}[a-zA-Z]{6}[A-Z0-9]{2}$"
EMAIL_REGEXP = r"^[\w.-]+@[\w.-]+\.\w+$"
PLAZA_REGEXP = r"^[a-zA-Z0-9]{1,24}$"
QUINCENA_REGEXP = r"^\d{6}$"
RFC_REGEXP = r"^[a-zA-Z]{3,4}\d{6}[a-zA-Z0-9]{3}$"
TOKEN_REGEXP = r"^[a-zA-Z0-9_.=+-]+$"


def safe_clave(input_str, max_len=16, only_digits=False, separator="-") -> str:
    """Safe clave"""
    if not isinstance(input_str, str):
        return ""
    stripped = input_str.strip()
    if stripped == "":
        return ""
    if only_digits:
        clean_string = re.sub(r"[^0-9]+", separator, stripped)
    else:
        clean_string = re.sub(r"[^a-zA-Z0-9]+", separator, unidecode(stripped))
    without_spaces = re.sub(r"\s+", "", clean_string)
    final = without_spaces.upper()
    if len(final) > max_len:
        return final[:max_len]
    return final


def safe_curp(input_str, is_optional=False, search_fragment=False) -> str:
    """Safe CURP"""
    if not isinstance(input_str, str):
        return ""
    stripped = input_str.strip()
    if is_optional and stripped == "":
        return ""
    clean_string = re.sub(r"[^a-zA-Z0-9]+", " ", unidecode(stripped))
    without_spaces = re.sub(r"\s+", "", clean_string)
    final = without_spaces.upper()
    if search_fragment is False and re.match(CURP_REGEXP, final) is None:
        raise ValueError("CURP inválida")
    return final


def safe_email(input_str, search_fragment=False) -> str:
    """Safe string"""
    if not isinstance(input_str, str):
        return ""
    final = input_str.strip().lower()
    if final == "":
        return ""
    if search_fragment:
        if re.match(r"^[\w.-]*@*[\w.-]*\.*\w*$", final) is None:
            return ""
        return final
    if re.match(EMAIL_REGEXP, final) is None:
        raise ValueError("E-mail inválido")
    return final


def safe_string(input_str, max_len=250, do_unidecode=True, save_enie=False, to_uppercase=True) -> str:
    """Safe string"""
    if not isinstance(input_str, str):
        return ""
    if do_unidecode:
        if save_enie:
            new_string = ""
            for char in input_str:
                if char == "ñ":
                    new_string += "ñ"
                elif char == "Ñ":
                    new_string += "Ñ"
                else:
                    new_string += unidecode(char)
            new_string = re.sub(r"[^a-zA-ZñÑ0-9.()/-]+", " ", new_string)  # ← línea agregada
        else:
            new_string = re.sub(r"[^a-zA-Z0-9.()/-]+", " ", unidecode(input_str))
    else:
        if save_enie is False:
            new_string = re.sub(r"[^a-záéíóúüA-ZÁÉÍÓÚÜ0-9.()/-]+", " ", input_str)
        else:
            new_string = re.sub(r"[^a-záéíóúüñA-ZÁÉÍÓÚÜÑ0-9.()/-]+", " ", input_str)
    removed_multiple_spaces = re.sub(r"\s+", " ", new_string)
    final = removed_multiple_spaces.strip()
    if to_uppercase:
        final = final.upper()
    if max_len == 0:
        return final
    return (final[:max_len] + "...") if len(final) > max_len else final


def safe_telefono(input_str) -> str:
    """Safe teléfono always ten digits"""
    if not isinstance(input_str, str) or input_str.strip() == "":
        return ""
    input_str = input_str.strip()
    only_digits = re.sub(r"[^0-9]", "", input_str)
    if len(only_digits) == 10:
        return only_digits
    return ""


def safe_uuid(uuid_string: str) -> uuid.UUID:
    """Safe UUID"""
    try:
        return uuid.UUID(uuid_string)
    except ValueError:
        raise ValueError(f"Invalid UUID: {uuid_string}")
