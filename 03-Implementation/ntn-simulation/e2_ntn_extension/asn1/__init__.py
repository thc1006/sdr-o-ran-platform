"""
ASN.1 PER Encoding for E2SM-NTN
================================

This module provides ASN.1 Packed Encoding Rules (PER) encoding/decoding
for E2SM-NTN messages.

API v1.1: Created to fix import path for validation script compatibility.

Author: Software Integration Specialist
Date: 2025-11-17
"""

# Import from parent directory (asn1_codec.py is in e2_ntn_extension/)
try:
    from ..asn1_codec import E2SM_NTN_ASN1_Codec, ASN1CodecError
except ImportError:
    # Fallback if relative import fails
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))

    try:
        from asn1_codec import E2SM_NTN_ASN1_Codec, ASN1CodecError
    except ImportError:
        # ASN.1 codec not available - create stub
        class ASN1CodecError(Exception):
            """ASN.1 codec error"""
            pass

        class E2SM_NTN_ASN1_Codec:
            """Stub ASN.1 codec - real implementation unavailable"""
            def __init__(self):
                import warnings
                warnings.warn(
                    "ASN.1 codec dependencies not available. "
                    "Falling back to JSON encoding.",
                    ImportWarning
                )

__all__ = ['E2SM_NTN_ASN1_Codec', 'ASN1CodecError']
__version__ = '1.1.0'
