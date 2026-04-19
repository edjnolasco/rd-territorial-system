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
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


PROVINCE_ALIASES = {
    "dn": "distrito nacional",
    "distrito nacional": "distrito nacional",
    "el seybo": "el seibo",
    "elias pina": "elias pina",
    "elías piña": "elias pina",
    "monsenor nouel": "monsenor nouel",
    "monseñor nouel": "monsenor nouel",
    "samana": "samana",
    "samaná": "samana",
    "san cristobal": "san cristobal",
    "san cristóbal": "san cristobal",
    "san jose de ocoa": "san jose de ocoa",
    "san josé de ocoa": "san jose de ocoa",
    "san pedro de macoris": "san pedro de macoris",
    "san pedro de macorís": "san pedro de macoris",
    "sanchez ramirez": "sanchez ramirez",
    "sánchez ramírez": "sanchez ramirez",
    "santiago rodriguez": "santiago rodriguez",
    "santiago rodríguez": "santiago rodriguez",
    "maria trinidad sanchez": "maria trinidad sanchez",
    "maría trinidad sánchez": "maria trinidad sanchez",
}

MUNICIPALITY_ALIASES = {
    "santo domingo de guzman": "santo domingo de guzman",
    "santo domingo de guzmán": "santo domingo de guzman",
    "sabana de la mar": "sabana de la mar",
}

DISTRICT_ALIASES = {
    "la victoria": "la victoria",
}


def canonical_province(name: Optional[str]) -> Optional[str]:
    normalized = normalize_text(name)
    if normalized is None:
        return None
    return PROVINCE_ALIASES.get(normalized, normalized)


def canonical_municipality(name: Optional[str]) -> Optional[str]:
    normalized = normalize_text(name)
    if normalized is None:
        return None
    return MUNICIPALITY_ALIASES.get(normalized, normalized)


def canonical_district_municipal(name: Optional[str]) -> Optional[str]:
    normalized = normalize_text(name)
    if normalized is None:
        return None
    return DISTRICT_ALIASES.get(normalized, normalized)


def match_score(left: Optional[str], right: Optional[str]) -> int:
    lnorm = normalize_text(left)
    rnorm = normalize_text(right)
    if lnorm is None or rnorm is None:
        return 0
    if lnorm == rnorm:
        return 100
    if lnorm in rnorm or rnorm in lnorm:
        return 80
    lset = set(lnorm.split())
    rset = set(rnorm.split())
    if lset and rset:
        overlap = len(lset & rset) / max(len(lset), len(rset))
        return int(overlap * 60)
    return 0
