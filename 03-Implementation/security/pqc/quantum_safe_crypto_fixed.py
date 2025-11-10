#!/usr/bin/env python3
"""
Quantum-Safe Cryptography for SDR-O-RAN Platform (FIXED VERSION)
實作 NIST 後量子密碼學標準 (修復版)

修復說明 (2025-11-10):
- 更新為 pqcrypto 0.3.4 的正確 API
- CRYSTALS-Kyber → ML-KEM (Module-Lattice KEM, FIPS 203)
- CRYSTALS-Dilithium → ML-DSA (Module-Lattice Digital Signature, FIPS 204)

Author: thc1006@ieee.org
Date: 2025-11-10
Status: WORKING (已修復並測試)
"""

import os
import sys
import logging
from typing import Tuple, Optional
from dataclasses import dataclass
import base64

# NIST PQC 函式庫 - 使用正確的導入方式
try:
    # ML-KEM (原 CRYSTALS-Kyber) - FIPS 203
    from pqcrypto.kem.ml_kem_1024 import (
        generate_keypair as ml_kem_generate_keypair,
        encrypt as ml_kem_encrypt,
        decrypt as ml_kem_decrypt
    )

    # ML-DSA (原 CRYSTALS-Dilithium) - FIPS 204
    from pqcrypto.sign.ml_dsa_87 import (
        generate_keypair as ml_dsa_generate_keypair,
        sign as ml_dsa_sign,
        verify as ml_dsa_verify
    )

    PQC_AVAILABLE = True
    print("✓ PQC 庫載入成功 (pqcrypto 0.3.4)")
except ImportError as e:
    PQC_AVAILABLE = False
    print(f"✗ PQC 庫載入失敗: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 資料結構
# =============================================================================

@dataclass
class PQCKeyPair:
    """後量子密碼學金鑰對"""
    algorithm: str  # "ml-kem-1024", "ml-dsa-87", etc.
    public_key: bytes
    secret_key: bytes
    security_level: int = 3  # NIST 安全等級 (1, 3, 或 5)

    def export_public_key_pem(self) -> str:
        """匯出 PEM 格式的公鑰"""
        b64 = base64.b64encode(self.public_key).decode()
        return f"-----BEGIN {self.algorithm.upper()} PUBLIC KEY-----\n{b64}\n-----END {self.algorithm.upper()} PUBLIC KEY-----"

    def export_secret_key_pem(self) -> str:
        """匯出 PEM 格式的私鑰 (敏感!)"""
        b64 = base64.b64encode(self.secret_key).decode()
        return f"-----BEGIN {self.algorithm.upper()} PRIVATE KEY-----\n{b64}\n-----END {self.algorithm.upper()} PRIVATE KEY-----"


@dataclass
class EncapsulatedKey:
    """KEM 封裝結果"""
    ciphertext: bytes  # 封裝的共享密鑰
    shared_secret: bytes  # 對稱金鑰 (用於 AES-256)


# =============================================================================
# ML-KEM (原 Kyber) - Key Encapsulation Mechanism
# =============================================================================

class MLKEM:
    """
    ML-KEM-1024 (原 CRYSTALS-Kyber-1024)
    NIST FIPS 203 標準
    安全等級: Level 5 (相當於 AES-256)
    """

    @staticmethod
    def generate_keypair() -> PQCKeyPair:
        """
        生成 ML-KEM-1024 金鑰對

        Returns:
            PQCKeyPair: 包含公鑰和私鑰
        """
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library not available")

        public_key, secret_key = ml_kem_generate_keypair()

        return PQCKeyPair(
            algorithm="ml-kem-1024",
            public_key=public_key,
            secret_key=secret_key,
            security_level=5  # NIST Level 5
        )

    @staticmethod
    def encapsulate(public_key: bytes) -> EncapsulatedKey:
        """
        封裝共享密鑰 (發送方使用)

        Args:
            public_key: 接收方的公鑰

        Returns:
            EncapsulatedKey: 包含密文和共享密鑰
        """
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library not available")

        # ML-KEM encrypt 返回 (ciphertext, shared_secret)
        ciphertext, shared_secret = ml_kem_encrypt(public_key)

        return EncapsulatedKey(
            ciphertext=ciphertext,
            shared_secret=shared_secret
        )

    @staticmethod
    def decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
        """
        解封裝共享密鑰 (接收方使用)

        Args:
            secret_key: 自己的私鑰
            ciphertext: 從發送方收到的密文

        Returns:
            bytes: 共享密鑰 (32 bytes for AES-256)
        """
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library not available")

        shared_secret = ml_kem_decrypt(secret_key, ciphertext)
        return shared_secret


# =============================================================================
# ML-DSA (原 Dilithium) - Digital Signatures
# =============================================================================

class MLDSA:
    """
    ML-DSA-87 (原 CRYSTALS-Dilithium5)
    NIST FIPS 204 標準
    安全等級: Level 5 (相當於 AES-256)
    """

    @staticmethod
    def generate_keypair() -> PQCKeyPair:
        """
        生成 ML-DSA-87 金鑰對

        Returns:
            PQCKeyPair: 包含公鑰和私鑰
        """
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library not available")

        public_key, secret_key = ml_dsa_generate_keypair()

        return PQCKeyPair(
            algorithm="ml-dsa-87",
            public_key=public_key,
            secret_key=secret_key,
            security_level=5  # NIST Level 5
        )

    @staticmethod
    def sign(message: bytes, secret_key: bytes) -> bytes:
        """
        對訊息進行簽章

        Args:
            message: 要簽章的訊息
            secret_key: 簽章者的私鑰

        Returns:
            bytes: signed_data (格式: message_length + message + signature)

        注意: pqcrypto 的 ml_dsa_sign 返回 detached signature（純簽章），
              為了保持 API 的便利性，我們將訊息和簽章打包在一起返回。
        """
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library not available")

        # ML-DSA sign 返回純簽章（detached mode）
        signature = ml_dsa_sign(secret_key, message)

        # 將訊息長度、訊息和簽章打包成 combined format
        # 格式: [message_length (4 bytes)] [message] [signature]
        import struct
        message_length = struct.pack('>I', len(message))  # 大端序，4 bytes
        signed_data = message_length + message + signature

        return signed_data

    @staticmethod
    def verify(signed_data: bytes, public_key: bytes) -> Tuple[bool, Optional[bytes]]:
        """
        驗證訊息簽章

        Args:
            signed_data: 簽章資料 (格式: message_length + message + signature)
            public_key: 簽章者的公鑰

        Returns:
            Tuple[bool, Optional[bytes]]: (驗證是否成功, 原始訊息)
        """
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library not available")

        try:
            import struct

            # 解析格式: [message_length (4 bytes)] [message] [signature]
            if len(signed_data) < 4:
                return (False, None)

            # 讀取訊息長度
            message_length = struct.unpack('>I', signed_data[:4])[0]

            # 提取訊息和簽章
            message = signed_data[4:4+message_length]
            signature = signed_data[4+message_length:]

            # 驗證簽章
            is_valid = ml_dsa_verify(public_key, message, signature)

            if is_valid:
                return (True, message)
            else:
                return (False, None)

        except Exception as e:
            logger.debug(f"ML-DSA verification error: {e}")
            return (False, None)


# =============================================================================
# 測試和示範
# =============================================================================

def test_ml_kem():
    """測試 ML-KEM 功能"""
    print("\n" + "="*70)
    print("測試 ML-KEM-1024 (Key Encapsulation)")
    print("="*70)

    try:
        # 1. 生成金鑰對
        print("1. 生成接收方金鑰對...")
        keypair = MLKEM.generate_keypair()
        print(f"   ✓ 公鑰大小: {len(keypair.public_key)} bytes")
        print(f"   ✓ 私鑰大小: {len(keypair.secret_key)} bytes")
        print(f"   ✓ 安全等級: NIST Level {keypair.security_level}")

        # 2. 發送方: 封裝共享密鑰
        print("\n2. 發送方封裝共享密鑰...")
        encap_result = MLKEM.encapsulate(keypair.public_key)
        print(f"   ✓ 密文大小: {len(encap_result.ciphertext)} bytes")
        print(f"   ✓ 共享密鑰: {len(encap_result.shared_secret)} bytes")
        print(f"   ✓ 共享密鑰 (hex): {encap_result.shared_secret.hex()[:32]}...")

        # 3. 接收方: 解封裝共享密鑰
        print("\n3. 接收方解封裝共享密鑰...")
        decap_shared_secret = MLKEM.decapsulate(
            keypair.secret_key,
            encap_result.ciphertext
        )
        print(f"   ✓ 解封裝成功")
        print(f"   ✓ 共享密鑰 (hex): {decap_shared_secret.hex()[:32]}...")

        # 4. 驗證共享密鑰相同
        if encap_result.shared_secret == decap_shared_secret:
            print("\n✅ ML-KEM 測試成功！雙方獲得相同的共享密鑰")
            return True
        else:
            print("\n✗ 錯誤：共享密鑰不匹配")
            return False

    except Exception as e:
        print(f"\n✗ ML-KEM 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_dsa():
    """測試 ML-DSA 功能"""
    print("\n" + "="*70)
    print("測試 ML-DSA-87 (Digital Signatures)")
    print("="*70)

    try:
        # 1. 生成金鑰對
        print("1. 生成簽章者金鑰對...")
        keypair = MLDSA.generate_keypair()
        print(f"   ✓ 公鑰大小: {len(keypair.public_key)} bytes")
        print(f"   ✓ 私鑰大小: {len(keypair.secret_key)} bytes")
        print(f"   ✓ 安全等級: NIST Level {keypair.security_level}")

        # 2. 簽章訊息
        message = b"Hello, this is a test message for PQC signature!"
        print(f"\n2. 對訊息進行簽章...")
        print(f"   訊息: {message.decode()}")
        signed_message = MLDSA.sign(message, keypair.secret_key)
        print(f"   ✓ 簽章訊息大小: {len(signed_message)} bytes")
        print(f"   ✓ 簽章後 (hex): {signed_message.hex()[:32]}...")

        # 3. 驗證簽章
        print("\n3. 驗證簽章...")
        is_valid, verified_msg = MLDSA.verify(signed_message, keypair.public_key)
        print(f"   ✓ 簽章驗證結果: {is_valid}")
        if is_valid:
            print(f"   ✓ 驗證後的訊息: {verified_msg.decode()}")

        # 4. 測試無效簽章
        print("\n4. 測試無效簽章...")
        wrong_signed_message = b"Invalid signed message"
        is_valid_wrong, _ = MLDSA.verify(wrong_signed_message, keypair.public_key)
        print(f"   ✓ 無效簽章驗證結果: {is_valid_wrong} (應該是 False)")

        if is_valid and not is_valid_wrong and verified_msg == message:
            print("\n✅ ML-DSA 測試成功！簽章功能正常")
            return True
        else:
            print("\n✗ 錯誤：簽章驗證邏輯有問題")
            print(f"   is_valid={is_valid}, is_valid_wrong={is_valid_wrong}")
            print(f"   verified_msg == message: {verified_msg == message if verified_msg else False}")
            return False

    except Exception as e:
        print(f"\n✗ ML-DSA 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程式"""
    print("="*70)
    print("SDR-O-RAN 平台 - 後量子密碼學測試 (修復版)")
    print("="*70)
    print(f"PQC 庫可用: {PQC_AVAILABLE}")

    if not PQC_AVAILABLE:
        print("\n✗ PQC 庫未可用，無法進行測試")
        print("請安裝: pip install pqcrypto")
        return False

    # 測試 ML-KEM
    kem_success = test_ml_kem()

    # 測試 ML-DSA
    dsa_success = test_ml_dsa()

    # 總結
    print("\n" + "="*70)
    print("測試總結")
    print("="*70)
    print(f"ML-KEM (Key Encapsulation): {'✅ PASS' if kem_success else '✗ FAIL'}")
    print(f"ML-DSA (Digital Signatures): {'✅ PASS' if dsa_success else '✗ FAIL'}")
    print("="*70)

    return kem_success and dsa_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
