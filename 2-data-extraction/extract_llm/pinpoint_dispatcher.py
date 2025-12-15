from typing import Callable, Dict
from ajp import AJP_pinpoint_imp
from ajsp import  AJSP_pinpoint_imp
from ajsrp import  AJSRP_pinpoint_imp
from am import AM_pinpoint_imp
from arpd import ARPD_pinpoint_imp


def AJP_pinpoint(page1: str, page2: str) -> str:
    return AJP_pinpoint_imp(page1, page2)

def AJSP_pinpoint(page1: str, page2: str) -> str:

    return AJSP_pinpoint_imp(page1, page2)

def ajsrp_pinpoint(page1: str, page2: str) -> str:
    # page 2 is unnecessary for AJSRP
    return AJSRP_pinpoint_imp(page1, "")

def AM_pinpoint(page1: str, page2: str) -> str:
    # TODO: tailor to AM tendencies
    return AM_pinpoint_imp(page1, page2)

def ARPD_pinpoint(page1: str, page2: str) -> str:
    # TODO: tailor to ARPD tendencies
    return ARPD_pinpoint_imp(page1, page2)

# =========================
# Dispatcher: pinpoint()
# =========================

_PINPOINTERS: Dict[str, Callable[[str, str], str]] = {
    "AJP": AJP_pinpoint,
    "AJSP": AJSP_pinpoint,
    "ajsrp": ajsrp_pinpoint,
    "AM": AM_pinpoint,
    "ARPD": ARPD_pinpoint,
}

def pinpoint(page1: str, page2: str, source: str) -> str:
    """
    Main entry point.
    Routes to a source-specific pinpointer based on `source`.
    If source is unknown, uses default_pinpoint.
    """
    src = (source or "").strip().upper()
    fn = _PINPOINTERS.get(src, None)
    if fn is None:
        return None # unknown source
    return fn(page1, page2)
