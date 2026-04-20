from __future__ import annotations

import re
import unicodedata
from typing import Optional


def normalize_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None

    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Normalizaciones previas útiles para RD
    text = text.replace("prov.", "prov")
    text = text.replace("sto.", "sto")
    text = text.replace("dgo.", "dgo")
    text = text.replace("dgo", "domingo")
    text = text.replace("mts", "matas")
    text = text.replace("hnas", "hermanas")
    text = text.replace("hnas.", "hermanas")

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


PROVINCE_ALIASES = {
    # Distrito Nacional / Santo Domingo
    "dn": "distrito nacional",
    "d n": "distrito nacional",
    "distrito nacional": "distrito nacional",
    "sto domingo": "santo domingo",
    "sto domingo este": "santo domingo",
    "sto dgo": "santo domingo",
    "sto dom": "santo domingo",
    "santo domingo": "santo domingo",
    "prov santo domingo": "santo domingo",

    # Provincias con variantes frecuentes
    "azua": "azua",
    "azua de compostela": "azua",

    "bahoruco": "bahoruco",
    "baoruco": "bahoruco",

    "barahona": "barahona",
    "dajabon": "dajabon",
    "dajabón": "dajabon",

    "duarte": "duarte",

    "el seibo": "el seibo",
    "seybo": "el seibo",
    "el seybo": "el seibo",

    "elias pina": "elias pina",
    "elias pinaa": "elias pina",
    "elias piña": "elias pina",

    "espaillat": "espaillat",

    "hato mayor": "hato mayor",
    "hato mayor del rey": "hato mayor",

    "hermanas mirabal": "hermanas mirabal",
    "salcedo": "hermanas mirabal",

    "independencia": "independencia",

    "la altagracia": "la altagracia",
    "altagracia": "la altagracia",

    "la romana": "la romana",
    "la vega": "la vega",
    "vega": "la vega",

    "maria trinidad sanchez": "maria trinidad sanchez",
    "maria trinidad sánchez": "maria trinidad sanchez",
    "m t sanchez": "maria trinidad sanchez",
    "mts": "maria trinidad sanchez",

    "monsenor nouel": "monsenor nouel",
    "monseñor nouel": "monsenor nouel",
    "bonao": "monsenor nouel",

    "monte cristi": "monte cristi",
    "montecristi": "monte cristi",

    "monte plata": "monte plata",

    "pedernales": "pedernales",
    "peravia": "peravia",
    "bani": "peravia",
    "bani": "peravia",

    "puerto plata": "puerto plata",

    "samana": "samana",
    "samaná": "samana",

    "san cristobal": "san cristobal",
    "san cristóbal": "san cristobal",

    "san jose de ocoa": "san jose de ocoa",
    "san jose ocoa": "san jose de ocoa",
    "san josé de ocoa": "san jose de ocoa",

    "san juan": "san juan",
    "san juan de la maguana": "san juan",

    "san pedro de macoris": "san pedro de macoris",
    "san pedro macoris": "san pedro de macoris",
    "san pedro de macorís": "san pedro de macoris",
    "spm": "san pedro de macoris",

    "sanchez ramirez": "sanchez ramirez",
    "sanchez ramírez": "sanchez ramirez",
    "cotui": "sanchez ramirez",
    "cotuí": "sanchez ramirez",

    "santiago": "santiago",
    "santiago rodriguez": "santiago rodriguez",
    "santiago rodríguez": "santiago rodriguez",
    "santiago rodriguez province": "santiago rodriguez",

    "valverde": "valverde",
    "mao": "valverde",
}


MUNICIPALITY_ALIASES = {
    # Santo Domingo / DN
    "santo domingo de guzman": "santo domingo de guzman",
    "santo domingo de guzmán": "santo domingo de guzman",
    "ciudad colonial": "santo domingo de guzman",
    "zona colonial": "santo domingo de guzman",

    "santo domingo este": "santo domingo este",
    "sde": "santo domingo este",

    "santo domingo norte": "santo domingo norte",
    "sdn": "santo domingo norte",

    "santo domingo oeste": "santo domingo oeste",
    "sdo": "santo domingo oeste",

    "los alcarrizos": "los alcarrizos",
    "pedro brand": "pedro brand",

    # Santiago
    "santiago de los caballeros": "santiago",
    "santiago": "santiago",

    # La Vega / cercanos
    "concepcion de la vega": "la vega",
    "concepción de la vega": "la vega",
    "la vega": "la vega",
    "jarabacoa": "jarabacoa",
    "constanza": "constanza",
    "jima abajo": "jima abajo",

    # San Cristóbal
    "san cristobal": "san cristobal",
    "san cristóbal": "san cristobal",
    "bajos de haina": "haina",
    "haina": "haina",

    # San Pedro de Macorís
    "san pedro de macoris": "san pedro de macoris",
    "san pedro de macorís": "san pedro de macoris",

    # Monseñor Nouel
    "bonao": "bonao",
    "maimon": "maimon",
    "mamon": "maimon",
    "piedra blanca": "piedra blanca",

    # Hermanas Mirabal
    "salcedo": "salcedo",
    "tenares": "tenares",
    "villa tapia": "villa tapia",

    # Puerto Plata
    "san felipe de puerto plata": "puerto plata",
    "puerto plata": "puerto plata",
    "sosua": "sosua",
    "sosúa": "sosua",

    # María Trinidad Sánchez
    "nagua": "nagua",

    # Hato Mayor
    "hato mayor del rey": "hato mayor",
    "hato mayor": "hato mayor",

    # Samaná
    "samana": "samana",
    "samaná": "samana",
    "las terrenas": "las terrenas",
    "sanchez": "sanchez",
    "sánchez": "sanchez",

    # El Seibo
    "el seibo": "el seibo",
    "el seybo": "el seibo",
    "miches": "miches",

    # Monte Cristi
    "san fernando de monte cristi": "monte cristi",
    "monte cristi": "monte cristi",
    "montecristi": "monte cristi",

    # Peravia
    "bani": "bani",
    "bani": "bani",

    # Valverde
    "mao": "mao",
    "esperanza": "esperanza",
    "laguna salada": "laguna salada",

    # Azua
    "azua": "azua",
    "azua de compostela": "azua",

    # Pedernales
    "pedernales": "pedernales",
    "oviedo": "oviedo",

    # Bahoruco
    "neyba": "neyba",
    "neiba": "neyba",
    "tamayo": "tamayo",

    # Independencia
    "jimani": "jimani",
    "jimaní": "jimani",
    "jimani ": "jimani",
    "jimaní": "jimani",
    "duverge": "duverge",
    "duvergé": "duverge",

    # Dajabón
    "dajabon": "dajabon",
    "dajabón": "dajabon",

    # Elías Piña
    "comendador": "comendador",
}


def canonical_province(name: Optional[str]) -> Optional[str]:
    normalized = normalize_text(name)
    if normalized is None or normalized == "":
        return None
    return PROVINCE_ALIASES.get(normalized, normalized)


def canonical_municipality(name: Optional[str]) -> Optional[str]:
    normalized = normalize_text(name)
    if normalized is None or normalized == "":
        return None
    return MUNICIPALITY_ALIASES.get(normalized, normalized)


def match_score(left: Optional[str], right: Optional[str]) -> int:
    lnorm = normalize_text(left)
    rnorm = normalize_text(right)

    if lnorm is None or rnorm is None:
        return 0

    if lnorm == rnorm:
        return 100

    lcanon_prov = canonical_province(lnorm)
    rcanon_prov = canonical_province(rnorm)
    if lcanon_prov == rcanon_prov:
        return 98

    lcanon_mun = canonical_municipality(lnorm)
    rcanon_mun = canonical_municipality(rnorm)
    if lcanon_mun == rcanon_mun:
        return 98

    if lnorm in rnorm or rnorm in lnorm:
        return 85

    lset = set(lnorm.split())
    rset = set(rnorm.split())
    if lset and rset:
        overlap = len(lset & rset) / max(len(lset), len(rset))
        return int(overlap * 70)

    return 0