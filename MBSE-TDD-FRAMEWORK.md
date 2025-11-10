# MBSE + TDD 開發框架
## 基於模型的系統工程 + 測試驅動開發

**創建日期**: 2025-11-10
**開發方法**: MBSE + TDD
**專案**: NTN SDR-O-RAN 平台

---

## MBSE 層級架構

```
系統需求 (System Requirements)
    ↓
功能需求 (Functional Requirements)
    ↓
組件規格 (Component Specifications)
    ↓
介面定義 (Interface Definitions)
    ↓
實現與測試 (Implementation & Testing)
    ↓
驗證與確認 (Verification & Validation)
```

---

## 第一層：系統需求 (SR)

### SR-001: NTN 衛星通訊能力
**需求**: 系統應能模擬 LEO 衛星通訊鏈路
**來源**: 3GPP Release 19 NTN 規範
**優先級**: P0 (最高)
**驗證方法**: 測試
**追溯到**: FR-001, FR-002, FR-003

### SR-002: O-RAN 架構合規
**需求**: 系統應符合 O-RAN Alliance 規範
**來源**: O-RAN.WG1.O-RAN Architecture Description
**優先級**: P0
**驗證方法**: 檢查
**追溯到**: FR-010, FR-011

### SR-003: 雲原生部署
**需求**: 系統應可部署於 Kubernetes
**來源**: 專案需求
**優先級**: P1
**驗證方法**: 測試
**追溯到**: FR-020

### SR-004: AI/ML 優化
**需求**: 系統應使用 DRL 進行網路優化
**來源**: 專案需求
**優先級**: P1
**驗證方法**: 測試
**追溯到**: FR-030

### SR-005: 後量子安全
**需求**: 系統應使用 NIST PQC 保護通訊
**來源**: 安全需求
**優先級**: P1
**驗證方法**: 測試
**追溯到**: FR-040

---

## 第二層：功能需求 (FR)

### FR-001: 衛星軌道計算
**需求**: 系統應能計算 LEO 衛星的即時位置和軌道參數
**父需求**: SR-001
**輸入**: TLE (Two-Line Element), 時間, 地面站位置
**輸出**: 衛星位置(緯度, 經度, 高度), 方位角, 仰角, 距離
**精度**: 位置誤差 < 1 km
**性能**: 計算時間 < 10 ms

**測試 (TDD)**:
```python
def test_satellite_orbit_computation():
    """測試衛星軌道計算"""
    tle = get_test_tle()
    station = ("25.0330 N", "121.5654 E")  # 台北
    time = datetime.now()

    orbit_calc = SatelliteOrbitCalculator(tle, station)
    result = orbit_calc.compute(time)

    # 驗證輸出存在
    assert 'latitude' in result
    assert 'longitude' in result
    assert 'altitude_km' in result
    assert 'azimuth_deg' in result
    assert 'elevation_deg' in result
    assert 'distance_km' in result

    # 驗證合理範圍
    assert -90 <= result['latitude'] <= 90
    assert -180 <= result['longitude'] <= 180
    assert 200 <= result['altitude_km'] <= 2000  # LEO 範圍
    assert 0 <= result['azimuth_deg'] < 360
    assert -90 <= result['elevation_deg'] <= 90

    # 驗證性能
    import time
    start = time.time()
    orbit_calc.compute(time)
    duration_ms = (time.time() - start) * 1000
    assert duration_ms < 10  # < 10 ms
```

### FR-002: 都卜勒頻移計算
**需求**: 系統應能計算衛星相對於地面站的都卜勒頻移
**父需求**: SR-001
**輸入**: 衛星速度向量, 地面站位置, 載波頻率
**輸出**: 都卜勒頻移 (Hz)
**精度**: ±100 Hz
**範圍**: -50 kHz ~ +50 kHz (Ku-band)

**測試 (TDD)**:
```python
def test_doppler_shift_calculation():
    """測試都卜勒頻移計算"""
    tle = get_test_tle()
    station = ("25.0330 N", "121.5654 E")
    carrier_freq_hz = 12.5e9  # 12.5 GHz

    doppler_calc = DopplerCalculator(tle, station, carrier_freq_hz)
    time = datetime.now()

    doppler_shift = doppler_calc.compute(time)

    # 驗證範圍
    assert -50000 <= doppler_shift <= 50000  # ±50 kHz

    # 驗證連續性（相近時間的都卜勒變化應該連續）
    time2 = time + timedelta(seconds=1)
    doppler_shift2 = doppler_calc.compute(time2)
    doppler_change_rate = abs(doppler_shift2 - doppler_shift)
    assert doppler_change_rate < 500  # 每秒變化 < 500 Hz（合理範圍）

    # 驗證極值情況（衛星遠離/接近）
    # 當衛星在地平線上升時，都卜勒應為正（接近）
    # 當衛星在地平線下降時，都卜勒應為負（遠離）
```

### FR-003: NTN 通道模型
**需求**: 系統應實現符合 3GPP 38.811 的 NTN 通道模型
**父需求**: SR-001
**輸入**: 衛星位置, 地面站位置, 頻率, 環境類型
**輸出**: 路徑損耗 (dB), 陰影衰落 (dB), 大氣衰減 (dB)
**精度**: 符合 3GPP 規範
**環境**: Dense Urban, Urban, Suburban, Rural

**測試 (TDD)**:
```python
def test_ntn_channel_model_path_loss():
    """測試 NTN 通道路徑損耗"""
    # 測試配置
    distance_km = 600  # LEO 衛星典型距離
    frequency_ghz = 12.5
    environment = "Rural"

    channel = NTNChannelModel(frequency_ghz, environment)
    path_loss_db = channel.compute_path_loss(distance_km)

    # 驗證自由空間路徑損耗公式
    # FSPL = 20*log10(d) + 20*log10(f) + 20*log10(4π/c) - Gtx - Grx
    expected_fspl = 20 * np.log10(distance_km * 1000) + \
                    20 * np.log10(frequency_ghz * 1e9) + \
                    20 * np.log10(4 * np.pi / 299792458)

    # 路徑損耗應該接近 FSPL（允許小幅度差異）
    assert abs(path_loss_db - expected_fspl) < 5  # ±5 dB 容差

    # 驗證損耗隨距離增加
    path_loss_1000km = channel.compute_path_loss(1000)
    assert path_loss_1000km > path_loss_db

def test_ntn_channel_model_shadow_fading():
    """測試陰影衰落"""
    channel = NTNChannelModel(12.5, "Urban")

    # 模擬 100 次，驗證統計特性
    shadow_fading_samples = []
    for _ in range(100):
        sf = channel.compute_shadow_fading(elevation_deg=45)
        shadow_fading_samples.append(sf)

    # Urban 環境：標準差應約為 4 dB（根據 3GPP 38.811）
    std_dev = np.std(shadow_fading_samples)
    assert 3 < std_dev < 5  # 允許誤差

    # 均值應接近 0
    mean = np.mean(shadow_fading_samples)
    assert abs(mean) < 1
```

### FR-004: 都卜勒補償
**需求**: 系統應能補償接收信號的都卜勒頻移
**父需求**: SR-001
**輸入**: IQ 樣本, 都卜勒頻移, 採樣率
**輸出**: 補償後的 IQ 樣本
**精度**: 殘餘頻偏 < 100 Hz
**延遲**: < 1 ms

**測試 (TDD)**:
```python
def test_doppler_compensation():
    """測試都卜勒補償"""
    # 生成測試信號
    sample_rate = 10e6  # 10 MSPS
    duration = 0.01  # 10 ms
    t = np.arange(0, duration, 1/sample_rate)

    # 原始信號：1 MHz 正弦波
    signal_freq = 1e6
    signal = np.exp(2j * np.pi * signal_freq * t)

    # 添加都卜勒頻移：+10 kHz
    doppler_shift = 10000
    doppler_signal = signal * np.exp(2j * np.pi * doppler_shift * t)

    # 補償
    compensator = DopplerCompensator(sample_rate)
    compensated = compensator.compensate(doppler_signal, doppler_shift)

    # 驗證：補償後應恢復原始頻率
    # 使用 FFT 檢查主要頻率成分
    fft = np.fft.fft(compensated)
    freqs = np.fft.fftfreq(len(compensated), 1/sample_rate)
    peak_freq = abs(freqs[np.argmax(np.abs(fft))])

    assert abs(peak_freq - signal_freq) < 100  # 殘餘頻偏 < 100 Hz

def test_doppler_compensation_performance():
    """測試都卜勒補償性能"""
    sample_rate = 10e6
    signal = np.random.randn(int(sample_rate * 0.001)) + \
             1j * np.random.randn(int(sample_rate * 0.001))  # 1 ms 資料

    compensator = DopplerCompensator(sample_rate)

    import time
    start = time.time()
    _ = compensator.compensate(signal, 10000)
    duration_ms = (time.time() - start) * 1000

    assert duration_ms < 1  # < 1 ms
```

### FR-005: Timing Advance 處理
**需求**: 系統應能處理 NTN 的 Timing Advance
**父需求**: SR-001
**輸入**: 傳播延遲, 採樣率
**輸出**: 調整後的時序
**精度**: < 1 樣本
**範圍**: 0 ~ 500 ms (GEO)

**測試 (TDD)**:
```python
def test_timing_advance_adjustment():
    """測試 Timing Advance 調整"""
    sample_rate = 10e6  # 10 MSPS
    propagation_delay_s = 0.004  # 4 ms (LEO 典型)

    # 生成測試信號
    signal = np.ones(1000, dtype=np.complex64)

    ta_adjuster = TimingAdvanceAdjuster(sample_rate)
    adjusted = ta_adjuster.adjust(signal, propagation_delay_s)

    # 驗證延遲樣本數
    expected_delay_samples = int(propagation_delay_s * sample_rate)
    actual_delay_samples = len(adjusted) - len(signal)

    assert abs(actual_delay_samples - expected_delay_samples) <= 1  # ±1 樣本

def test_timing_advance_geg_satellite():
    """測試 GEO 衛星的 Timing Advance"""
    sample_rate = 10e6
    propagation_delay_s = 0.270  # 270 ms (GEO)

    signal = np.ones(1000, dtype=np.complex64)

    ta_adjuster = TimingAdvanceAdjuster(sample_rate)
    adjusted = ta_adjuster.adjust(signal, propagation_delay_s)

    expected_delay_samples = int(propagation_delay_s * sample_rate)
    actual_delay_samples = len(adjusted) - len(signal)

    assert abs(actual_delay_samples - expected_delay_samples) <= 1
```

---

## 第三層：組件規格

### Component-001: SatelliteOrbitCalculator
**功能**: 計算衛星軌道參數
**依賴**: Skyfield 庫
**介面**:
```python
class SatelliteOrbitCalculator:
    def __init__(self, tle: Tuple[str, str], ground_station: Tuple[str, str]):
        pass

    def compute(self, time: datetime) -> Dict[str, float]:
        """
        Returns:
            {
                'latitude': float,      # 度
                'longitude': float,     # 度
                'altitude_km': float,   # km
                'azimuth_deg': float,   # 度
                'elevation_deg': float, # 度
                'distance_km': float    # km
            }
        """
        pass
```

### Component-002: DopplerCalculator
**功能**: 計算都卜勒頻移
**依賴**: SatelliteOrbitCalculator
**介面**:
```python
class DopplerCalculator:
    def __init__(self, tle: Tuple[str, str], ground_station: Tuple[str, str],
                 carrier_freq_hz: float):
        pass

    def compute(self, time: datetime) -> float:
        """Returns: Doppler shift in Hz"""
        pass

    def compute_rate(self, time: datetime) -> float:
        """Returns: Doppler rate in Hz/s"""
        pass
```

### Component-003: NTNChannelModel
**功能**: 3GPP 38.811 NTN 通道模型
**依賴**: 無
**介面**:
```python
class NTNChannelModel:
    def __init__(self, frequency_ghz: float, environment: str):
        """
        Args:
            frequency_ghz: Carrier frequency in GHz
            environment: "Dense Urban", "Urban", "Suburban", "Rural"
        """
        pass

    def compute_path_loss(self, distance_km: float, elevation_deg: float = 90) -> float:
        """Returns: Path loss in dB"""
        pass

    def compute_shadow_fading(self, elevation_deg: float) -> float:
        """Returns: Shadow fading in dB"""
        pass

    def compute_atmospheric_loss(self, elevation_deg: float, frequency_ghz: float) -> float:
        """Returns: Atmospheric attenuation in dB"""
        pass

    def compute_total_loss(self, distance_km: float, elevation_deg: float) -> float:
        """Returns: Total channel loss in dB"""
        pass
```

### Component-004: DopplerCompensator
**功能**: 補償都卜勒頻移
**依賴**: NumPy
**介面**:
```python
class DopplerCompensator:
    def __init__(self, sample_rate: float):
        pass

    def compensate(self, signal: np.ndarray, doppler_shift_hz: float) -> np.ndarray:
        """
        Args:
            signal: Complex IQ samples
            doppler_shift_hz: Doppler shift to compensate

        Returns:
            Compensated signal
        """
        pass
```

### Component-005: TimingAdvanceAdjuster
**功能**: 調整 Timing Advance
**依賴**: NumPy
**介面**:
```python
class TimingAdvanceAdjuster:
    def __init__(self, sample_rate: float):
        pass

    def adjust(self, signal: np.ndarray, propagation_delay_s: float) -> np.ndarray:
        """
        Args:
            signal: Input signal
            propagation_delay_s: Propagation delay in seconds

        Returns:
            Timing-adjusted signal
        """
        pass
```

---

## TDD 開發流程

### 步驟 1：編寫失敗的測試
```bash
# 創建測試文件
touch tests/test_satellite_orbit.py

# 編寫測試（測試會失敗，因為還沒實現）
pytest tests/test_satellite_orbit.py
# FAILED
```

### 步驟 2：實現最小代碼使測試通過
```bash
# 實現組件
vim src/satellite_orbit_calculator.py

# 運行測試
pytest tests/test_satellite_orbit.py
# PASSED
```

### 步驟 3：重構
```bash
# 優化代碼質量
# 重新運行測試確保沒有破壞
pytest tests/
```

### 步驟 4：重複
繼續下一個組件...

---

## 測試覆蓋率目標

- **單元測試**: 100% 覆蓋所有組件
- **整合測試**: 100% 覆蓋所有介面
- **系統測試**: 100% 覆蓋所有功能需求
- **驗收測試**: 100% 覆蓋所有系統需求

---

## 追溯矩陣

| 系統需求 | 功能需求 | 組件 | 測試 | 狀態 |
|---------|---------|------|------|------|
| SR-001 | FR-001 | Component-001 | test_satellite_orbit_computation | ⏳ 待實施 |
| SR-001 | FR-002 | Component-002 | test_doppler_shift_calculation | ⏳ 待實施 |
| SR-001 | FR-003 | Component-003 | test_ntn_channel_model | ⏳ 待實施 |
| SR-001 | FR-004 | Component-004 | test_doppler_compensation | ⏳ 待實施 |
| SR-001 | FR-005 | Component-005 | test_timing_advance_adjustment | ⏳ 待實施 |

---

## 下一步

1. **設置測試環境**
2. **創建測試文件結構**
3. **逐一實現組件（TDD）**
4. **驗證追溯性**
5. **生成MBSE模型（SysML）**

**創建日期**: 2025-11-10
**狀態**: 框架完成，準備開始實施
