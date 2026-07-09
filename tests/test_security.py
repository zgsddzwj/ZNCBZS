"""
安全模块单元测试
"""
import pytest
from backend.core.security import (
    encrypt_data,
    decrypt_data,
    IPWhitelist,
    get_client_ip,
)


class TestEncryption:
    """加密/解密测试"""

    def test_encrypt_and_decrypt(self):
        """测试加密后解密还原"""
        original = "sensitive_data_123"
        encrypted = encrypt_data(original)
        assert encrypted != original
        decrypted = decrypt_data(encrypted)
        assert decrypted == original

    def test_encrypt_different_each_time(self):
        """测试每次加密结果不同（Fernet 随机性）"""
        data = "same_data"
        enc1 = encrypt_data(data)
        enc2 = encrypt_data(data)
        assert enc1 != enc2
        # 但都能正确解密
        assert decrypt_data(enc1) == data
        assert decrypt_data(enc2) == data

    def test_encrypt_empty_string(self):
        """测试空字符串加密"""
        encrypted = encrypt_data("")
        assert decrypt_data(encrypted) == ""


class TestIPWhitelist:
    """IP 白名单测试"""

    def test_disabled_allows_all(self):
        """测试未启用时允许所有 IP"""
        wl = IPWhitelist()
        wl.enabled = False
        assert wl.is_allowed("192.168.1.1") is True

    def test_enabled_allows_listed(self):
        """测试启用时仅允许白名单 IP"""
        wl = IPWhitelist()
        wl.enabled = True
        wl.add_ip("10.0.0.1")
        assert wl.is_allowed("10.0.0.1") is True
        assert wl.is_allowed("10.0.0.2") is False

    def test_localhost_always_allowed(self):
        """测试本地回环地址始终允许"""
        wl = IPWhitelist()
        wl.enabled = True
        assert wl.is_allowed("127.0.0.1") is True
        assert wl.is_allowed("::1") is True

    def test_remove_ip(self):
        """测试移除 IP"""
        wl = IPWhitelist()
        wl.enabled = True
        wl.add_ip("10.0.0.5")
        assert wl.is_allowed("10.0.0.5") is True
        wl.remove_ip("10.0.0.5")
        assert wl.is_allowed("10.0.0.5") is False
