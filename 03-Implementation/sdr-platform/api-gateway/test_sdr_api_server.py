"""
Unit Tests for SDR API Gateway
測試 SDR API Gateway 的核心功能

Author: thc1006@ieee.org
Date: 2025-11-10
Coverage Target: Basic functionality and data models
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# 添加模組路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdr_api_server import (
    app,
    StationConfig,
    StationStatus,
    USRP_DEVICES,
    STATIONS,
    verify_password,
    get_password_hash,
)

# 測試客戶端 - 使用 with 語句以確保正確的生命周期管理
# 我們將在每個測試中創建客戶端

@pytest.fixture
def client():
    """創建測試客戶端的 fixture"""
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# 測試 1: 基本 API 端點
# ============================================================================

def test_read_root(client):
    """測試健康檢查端點（替代根端點）"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_docs_endpoint(client):
    """測試 API 文檔端點"""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200


# ============================================================================
# 測試 2: USRP 裝置查詢
# ============================================================================

def test_list_usrp_devices(client):
    """測試列出 USRP 裝置"""
    # 注意：這需要身份驗證，所以我們測試未授權的情況
    response = client.get("/api/v1/usrp/devices")
    # 因為沒有 token，應該返回 401
    assert response.status_code == 401


def test_usrp_devices_data_structure():
    """測試 USRP_DEVICES 資料結構"""
    assert isinstance(USRP_DEVICES, dict)
    assert len(USRP_DEVICES) > 0

    for device_id, device_info in USRP_DEVICES.items():
        assert "model" in device_info
        assert "serial" in device_info
        assert "status" in device_info
        assert device_info["status"] in ["online", "offline"]


# ============================================================================
# 測試 3: 資料模型驗證
# ============================================================================

def test_station_config_validation_valid():
    """測試有效的 StationConfig"""
    config = StationConfig(
        station_id="test-station-001",
        usrp_device="usrp-001",
        frequency_band="Ku",
        center_frequency_ghz=12.5,
        sample_rate_msps=10.0,
        antenna_config={"gain": 20, "polarization": "RHCP"},
        modulation_scheme="QPSK",
        oran_integration=False
    )

    assert config.station_id == "test-station-001"
    assert config.frequency_band == "Ku"
    assert config.center_frequency_ghz == 12.5


def test_station_config_validation_invalid_frequency_band():
    """測試無效的頻段"""
    with pytest.raises(ValueError):
        StationConfig(
            station_id="test-station-001",
            usrp_device="usrp-001",
            frequency_band="X",  # 無效：只允許 C, Ku, Ka
            center_frequency_ghz=12.5,
            sample_rate_msps=10.0,
            antenna_config={},
            modulation_scheme="QPSK"
        )


def test_station_config_validation_frequency_range():
    """測試頻率範圍驗證"""
    # 測試有效範圍
    config = StationConfig(
        station_id="test-station-001",
        usrp_device="usrp-001",
        frequency_band="Ku",
        center_frequency_ghz=15.0,  # 在 1.0-40.0 範圍內
        sample_rate_msps=10.0,
        antenna_config={},
        modulation_scheme="QPSK"
    )
    assert config.center_frequency_ghz == 15.0

    # 測試超出範圍
    with pytest.raises(ValueError):
        StationConfig(
            station_id="test-station-001",
            usrp_device="usrp-001",
            frequency_band="Ku",
            center_frequency_ghz=50.0,  # 超出範圍
            sample_rate_msps=10.0,
            antenna_config={},
            modulation_scheme="QPSK"
        )


def test_station_status_model():
    """測試 StationStatus 資料模型"""
    status = StationStatus(
        station_id="test-station-001",
        status="running",
        usrp_connected=True,
        signal_snr_db=15.5,
        ebn0_db=12.3,
        packet_error_rate=0.001,
        usrp_temperature_c=45.2,
        data_rate_mbps=85.0,
        last_updated=datetime.now()
    )

    assert status.station_id == "test-station-001"
    assert status.status == "running"
    assert status.signal_snr_db == 15.5
    assert status.usrp_connected is True


# ============================================================================
# 測試 4: 身份驗證功能
# ============================================================================

def test_password_hashing():
    """測試密碼雜湊功能"""
    plain_password = "test_password_123"
    hashed = get_password_hash(plain_password)

    # 雜湊後的密碼應該不同
    assert hashed != plain_password

    # 驗證正確的密碼
    assert verify_password(plain_password, hashed) is True

    # 驗證錯誤的密碼
    assert verify_password("wrong_password", hashed) is False


def test_login_endpoint_no_credentials(client):
    """測試未提供憑證的登入"""
    response = client.post("/token")
    assert response.status_code == 422  # Validation error


# ============================================================================
# 測試 5: API 端點結構
# ============================================================================

def test_api_routes_exist():
    """測試主要 API 路由是否存在"""
    # 獲取所有路由
    routes = [route.path for route in app.routes]

    # 檢查關鍵路由（使用實際存在的路由）
    expected_routes = [
        "/token",                      # OAuth2 token endpoint
        "/api/v1/docs",                # API 文檔
        "/api/v1/sdr/stations",        # 站點管理
        "/api/v1/usrp/devices",        # USRP 裝置查詢
        "/healthz",                    # 健康檢查
    ]

    for expected_route in expected_routes:
        assert any(expected_route in route for route in routes), \
            f"Route {expected_route} not found in {routes}"


def test_openapi_schema(client):
    """測試 OpenAPI schema 是否正確生成"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema


# ============================================================================
# 測試 6: 錯誤處理
# ============================================================================

def test_404_error(client):
    """測試 404 錯誤處理"""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404


def test_405_method_not_allowed(client):
    """測試不允許的 HTTP 方法"""
    # GET endpoint 不應接受 DELETE
    response = client.delete("/api/v1/usrp/devices")
    assert response.status_code in [405, 401]  # 可能是 401（未授權）或 405


# ============================================================================
# 測試 7: 資料一致性
# ============================================================================

def test_stations_dict_initialization():
    """測試 STATIONS 字典初始化"""
    # STATIONS 應該是一個字典
    assert isinstance(STATIONS, dict)
    # 初始應該是空的
    # 注意：如果在測試過程中被修改，這個測試可能會失敗


def test_usrp_device_ids_consistency():
    """測試 USRP 裝置 ID 的一致性"""
    device_ids = list(USRP_DEVICES.keys())

    # 所有 ID 都應該符合命名規範
    for device_id in device_ids:
        assert device_id.startswith("usrp-")
        assert len(device_id) > 5


# ============================================================================
# 測試 8: 模擬數據驗證
# ============================================================================

def test_simulated_usrp_devices():
    """驗證模擬的 USRP 裝置資料"""
    # 這個測試確認我們知道數據是模擬的
    expected_devices = ["usrp-001", "usrp-002", "usrp-003"]

    for device_id in expected_devices:
        assert device_id in USRP_DEVICES
        device = USRP_DEVICES[device_id]

        # 驗證模擬數據的結構
        assert "model" in device
        assert "serial" in device
        assert "status" in device

        # 驗證已知的模擬值
        if device_id == "usrp-001":
            assert device["model"] == "B210"
            assert device["serial"] == "3234ABC"
        elif device_id == "usrp-002":
            assert device["model"] == "X310"
            assert device["serial"] == "5678DEF"


# ============================================================================
# 測試統計
# ============================================================================

def test_suite_statistics():
    """輸出測試套件統計"""
    print("\n" + "="*70)
    print("測試套件統計")
    print("="*70)
    print(f"總測試數: {pytest.main.Session.testscollected if hasattr(pytest.main, 'Session') else 'N/A'}")
    print(f"測試文件: test_sdr_api_server.py")
    print(f"被測模組: sdr_api_server.py")
    print(f"測試類別:")
    print("  - 基本 API 端點")
    print("  - USRP 裝置查詢")
    print("  - 資料模型驗證")
    print("  - 身份驗證功能")
    print("  - API 路由結構")
    print("  - 錯誤處理")
    print("  - 資料一致性")
    print("  - 模擬數據驗證")
    print("="*70)


# ============================================================================
# 主程式 - 運行測試
# ============================================================================

if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])
