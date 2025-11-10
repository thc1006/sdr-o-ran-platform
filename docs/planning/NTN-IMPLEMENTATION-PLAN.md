# NTN 衛星通訊專案完整實施計劃
## 基於雲原生之 SDR 基頻處理地面站和 O-RAN 基站整合應用於 NTN 通訊

**專案性質**: 3GPP Release 19 NTN (Non-Terrestrial Networks) 合規實現
**創建日期**: 2025-11-10
**目標**: 完整實現衛星通訊地面站，符合 3GPP NTN 規範

---

## 執行摘要

**專案核心**:
整合軟體定義無線電（SDR）衛星地面站與雲原生 O-RAN 架構，應用於非地面網路（NTN）通訊。

**關鍵挑戰**:
1. **高延遲**: GEO 衛星 ~270ms, LEO 衛星 ~20-40ms
2. **都卜勒效應**: LEO 衛星移動速度 7.5 km/s，造成頻率偏移 ±40 kHz (Ku-band)
3. **大覆蓋範圍**: 單一衛星覆蓋半徑 500-1000 km
4. **動態鏈路**: 衛星位置持續變化，需要預測和補償
5. **時序調整**: Timing Advance 需要精確計算（基於衛星軌道）

**可用資源**:
- CPU: 30 cores ✅
- RAM: 47GB (43GB 可用) ✅
- 磁碟: 222GB 可用 ✅
- Docker & Kubernetes: 已就緒 ✅

**預估時間**: 4-6 個月（嚴謹開發）
**預估成本**: $0（全開源，無需硬體，使用衛星資料模擬）

---

## NTN 特殊需求分析

### 1. 衛星軌道類型

#### GEO (Geostationary Earth Orbit)
- **高度**: 35,786 km
- **覆蓋範圍**: ~1/3 地球表面
- **延遲**: ~270 ms (單程)
- **都卜勒**: 幾乎為 0（相對靜止）
- **適用**: 固定覆蓋、廣播

#### LEO (Low Earth Orbit)
- **高度**: 500-2000 km
- **覆蓋範圍**: 500-1000 km 半徑
- **延遲**: 20-40 ms
- **都卜勒**: ±10-40 kHz（視頻段而定）
- **移動速度**: ~7.5 km/s
- **軌道週期**: 90-120 分鐘
- **適用**: 低延遲通訊、IoT

#### MEO (Medium Earth Orbit)
- **高度**: 2,000-35,786 km
- **延遲**: 70-125 ms
- **適用**: 導航（GPS, Galileo）

### 2. 頻段

本專案使用 **Ku-band**:
- **上行**: 14.0-14.5 GHz
- **下行**: 12.5-12.75 GHz
- **頻寬**: 500 MHz

### 3. NTN 特定技術挑戰

#### 3.1 時序調整（Timing Advance）
```python
# 3GPP 38.821 公式
TA = 2 × (satellite_altitude / c) + propagation_delay
# GEO: TA ~270 ms
# LEO (600 km): TA ~4 ms
```

#### 3.2 都卜勒補償
```python
# 最大都卜勒頻偏 (Ku-band, LEO)
doppler_shift = (v_satellite / c) × f_carrier
# v_satellite = 7.5 km/s
# f_carrier = 12.5 GHz
# doppler_shift = ±31.25 kHz
```

#### 3.3 路徑損耗
```python
# 自由空間路徑損耗 (Ku-band, LEO 600 km)
FSPL = 20 × log10(d) + 20 × log10(f) + 20 × log10(4π/c)
# d = 600 km, f = 12.5 GHz
# FSPL ≈ 189 dB
```

---

## 階段性實施計劃

### 階段 0：環境準備和理論驗證（1週）✅ 可立即開始

#### 目標：確保所有工具和理論模型正確

#### 0.1 安裝和驗證核心工具

**ns-3 + NTN 模組**:
```bash
# 安裝 ns-3.43（最新版本）
cd ~
git clone https://gitlab.com/nsnam/ns-3-dev.git ns-3
cd ns-3

# 安裝依賴
sudo apt-get update
sudo apt-get install -y gcc g++ python3 python3-dev \
    cmake ninja-build ccache libgsl-dev libsqlite3-dev \
    libboost-all-dev libgtk-3-dev

# 配置
./ns3 configure --enable-examples --enable-tests

# 建置
./ns3 build

# 測試
./ns3 run first
```

**5G-LENA (5G NR 模組)**:
```bash
cd ~/ns-3/contrib
git clone https://gitlab.com/cttc-lena/nr.git

cd ..
./ns3 configure --enable-examples --enable-tests
./ns3 build
```

**ns-O-RAN (O-RAN E2 介面)**:
```bash
cd ~/ns-3/contrib
git clone https://github.com/wineslab/ns-o-ran-ns3-mmwave.git ns-o-ran

cd ..
./ns3 configure --enable-examples --enable-tests
./ns3 build
```

**驗證**:
```bash
# 測試 5G NR 場景
./ns3 run cttc-3gpp-channel-example

# 測試 O-RAN E2
./ns3 run ns-o-ran-example
```

#### 0.2 衛星軌道計算工具

**安裝 Skyfield（精確的衛星軌道計算）**:
```bash
pip3 install --user skyfield numpy scipy matplotlib
```

**測試衛星軌道預測**:
```python
from skyfield.api import load, Topos, EarthSatellite

# 載入時間和地球資料
ts = load.timescale()
planets = load('de421.bsp')
earth = planets['earth']

# 定義地面站位置（台灣）
station = Topos('25.0330 N', '121.5654 E')  # 台北

# LEO 衛星 TLE（Two-Line Element）範例
line1 = '1 43078U 17073A   23365.16928945  .00000000  00000-0  00000-0 0  9999'
line2 = '2 43078  97.4000  59.5000 0001500  90.0000 270.0000 15.20000000    16'

satellite = EarthSatellite(line1, line2, 'Test LEO', ts)

# 計算當前時間的衛星位置
t = ts.now()
geocentric = satellite.at(t)
subpoint = geocentric.subpoint()

print(f"衛星高度: {subpoint.elevation.km:.2f} km")
print(f"緯度: {subpoint.latitude.degrees:.2f}°")
print(f"經度: {subpoint.longitude.degrees:.2f}°")

# 計算相對於地面站的方位和仰角
difference = satellite - station
topocentric = difference.at(t)
alt, az, distance = topocentric.altaz()

print(f"方位角: {az.degrees:.2f}°")
print(f"仰角: {alt.degrees:.2f}°")
print(f"距離: {distance.km:.2f} km")

# 計算都卜勒頻移
velocity = topocentric.velocity.km_per_s
radial_velocity = velocity[2]  # 徑向速度
f_carrier = 12.5e9  # 12.5 GHz
c = 299792.458  # km/s
doppler_shift = (radial_velocity / c) * f_carrier

print(f"徑向速度: {radial_velocity:.2f} km/s")
print(f"都卜勒頻移: {doppler_shift / 1000:.2f} kHz")
```

#### 0.3 驗證標準
- [ ] ns-3 成功安裝並運行
- [ ] 5G-LENA 範例成功執行
- [ ] ns-O-RAN E2 介面正常工作
- [ ] Skyfield 可以計算衛星軌道
- [ ] 都卜勒頻移計算正確

---

### 階段 1：NTN 通道模型實現（2週）

#### 目標：實現符合 3GPP 38.811 的 NTN 通道模型

#### 1.1 NTN 通道特性

**3GPP 38.811 NTN 通道模型**:
- Dense Urban (DU)
- Urban (U)
- Suburban (SU)
- Rural (R)

**需要實現的通道特性**:
1. **路徑損耗**:
   - 自由空間路徑損耗（FSPL）
   - 陰影衰落（Shadow Fading）
   - 大氣吸收（Atmospheric Attenuation）
   - 雨衰（Rain Attenuation）

2. **都卜勒效應**:
   - 基於衛星速度的頻率偏移
   - 時變通道

3. **延遲**:
   - 傳播延遲
   - Timing Advance

**實現方案**:
```python
# ntn_channel_model.py
import numpy as np
from skyfield.api import load, EarthSatellite, Topos

class NTNChannelModel:
    """
    3GPP 38.811 NTN 通道模型
    """
    def __init__(self, satellite_tle, ground_station_location, frequency_ghz):
        self.ts = load.timescale()
        self.satellite = EarthSatellite(*satellite_tle, 'LEO', self.ts)
        self.ground_station = Topos(*ground_station_location)
        self.frequency = frequency_ghz * 1e9  # Hz

    def compute_link_parameters(self, time):
        """
        計算鏈路參數
        """
        # 衛星-地面站幾何
        difference = self.satellite - self.ground_station
        topocentric = difference.at(time)
        alt, az, distance = topocentric.altaz()

        # 1. 路徑損耗（FSPL）
        fspl_db = 20 * np.log10(distance.km * 1000) + \
                  20 * np.log10(self.frequency) + \
                  20 * np.log10(4 * np.pi / 299792458)

        # 2. 都卜勒頻移
        velocity = topocentric.velocity.km_per_s
        radial_velocity = velocity[2]  # km/s
        doppler_shift_hz = (radial_velocity * 1000 / 299792458) * self.frequency

        # 3. 傳播延遲
        propagation_delay_s = distance.km * 1000 / 299792458

        # 4. 仰角（用於計算陰影衰落）
        elevation_deg = alt.degrees

        # 5. 陰影衰落（簡化模型）
        if elevation_deg > 60:
            shadow_fading_db = np.random.normal(0, 1)  # Rural
        elif elevation_deg > 30:
            shadow_fading_db = np.random.normal(0, 2)  # Suburban
        else:
            shadow_fading_db = np.random.normal(0, 4)  # Urban

        # 6. 大氣吸收（Ku-band, 簡化）
        atmospheric_loss_db = 0.1 * (90 - elevation_deg) / 90  # 簡化模型

        return {
            'distance_km': distance.km,
            'elevation_deg': elevation_deg,
            'azimuth_deg': az.degrees,
            'fspl_db': fspl_db,
            'shadow_fading_db': shadow_fading_db,
            'atmospheric_loss_db': atmospheric_loss_db,
            'total_loss_db': fspl_db + shadow_fading_db + atmospheric_loss_db,
            'doppler_shift_hz': doppler_shift_hz,
            'propagation_delay_s': propagation_delay_s,
            'radial_velocity_m_s': radial_velocity * 1000
        }

# 測試
if __name__ == '__main__':
    # LEO 衛星 TLE（範例）
    tle = (
        '1 43078U 17073A   23365.16928945  .00000000  00000-0  00000-0 0  9999',
        '2 43078  97.4000  59.5000 0001500  90.0000 270.0000 15.20000000    16'
    )

    # 台灣地面站
    location = ('25.0330 N', '121.5654 E')

    # Ku-band 下行頻率
    freq_ghz = 12.5

    model = NTNChannelModel(tle, location, freq_ghz)

    ts = load.timescale()
    t = ts.now()

    params = model.compute_link_parameters(t)

    print("=== NTN 鏈路參數 ===")
    print(f"距離: {params['distance_km']:.2f} km")
    print(f"仰角: {params['elevation_deg']:.2f}°")
    print(f"方位角: {params['azimuth_deg']:.2f}°")
    print(f"FSPL: {params['fspl_db']:.2f} dB")
    print(f"陰影衰落: {params['shadow_fading_db']:.2f} dB")
    print(f"總損耗: {params['total_loss_db']:.2f} dB")
    print(f"都卜勒頻移: {params['doppler_shift_hz'] / 1000:.2f} kHz")
    print(f"傳播延遲: {params['propagation_delay_s'] * 1000:.2f} ms")
```

#### 1.2 整合到 ns-3

**創建 NTN 通道模組**:
```cpp
// ntn-channel-model.h
#include "ns3/propagation-loss-model.h"

namespace ns3 {

class NtnChannelModel : public PropagationLossModel
{
public:
  static TypeId GetTypeId (void);
  NtnChannelModel ();
  virtual ~NtnChannelModel ();

  void SetSatelliteTle (std::string line1, std::string line2);
  void SetGroundStationLocation (double latitude, double longitude);
  void SetFrequency (double frequencyGHz);

private:
  virtual double DoCalcRxPower (double txPowerDbm,
                                Ptr<MobilityModel> a,
                                Ptr<MobilityModel> b) const;

  // Python 橋接，使用 Skyfield
  double ComputePathLoss (double time) const;
  double ComputeDopplerShift (double time) const;
};

} // namespace ns3
```

#### 1.3 驗證標準
- [ ] NTN 通道模型正確實現
- [ ] 路徑損耗計算符合 3GPP 38.811
- [ ] 都卜勒頻移計算正確
- [ ] 可以模擬衛星移動造成的通道變化

---

### 階段 2：GNU Radio NTN 信號處理鏈（2週）

#### 目標：實現完整的 NTN SDR 信號處理

#### 2.1 NTN 特定信號處理模組

**需要實現的模組**:
1. **都卜勒補償**:
   ```python
   class DopplerCompensator(gr.sync_block):
       """都卜勒頻移補償"""
       def __init__(self, sample_rate, center_freq):
           gr.sync_block.__init__(
               self,
               name="Doppler Compensator",
               in_sig=[np.complex64],
               out_sig=[np.complex64]
           )
           self.sample_rate = sample_rate
           self.center_freq = center_freq
           self.doppler_shift = 0  # 從衛星軌道計算獲得

       def set_doppler_shift(self, shift_hz):
           self.doppler_shift = shift_hz

       def work(self, input_items, output_items):
           in0 = input_items[0]
           out = output_items[0]

           # 生成補償相位
           t = np.arange(len(in0)) / self.sample_rate
           phase = 2 * np.pi * self.doppler_shift * t
           compensation = np.exp(-1j * phase)

           out[:] = in0 * compensation
           return len(output_items[0])
   ```

2. **Timing Advance 處理**:
   ```python
   class TimingAdvanceAdjuster(gr.sync_block):
       """時序提前調整"""
       def __init__(self, sample_rate):
           gr.sync_block.__init__(
               self,
               name="Timing Advance Adjuster",
               in_sig=[np.complex64],
               out_sig=[np.complex64]
           )
           self.sample_rate = sample_rate
           self.timing_advance_samples = 0

       def set_timing_advance(self, delay_seconds):
           self.timing_advance_samples = int(delay_seconds * self.sample_rate)

       def work(self, input_items, output_items):
           in0 = input_items[0]
           out = output_items[0]

           # 簡化：添加延遲
           if len(in0) > self.timing_advance_samples:
               out[:] = np.pad(in0, (self.timing_advance_samples, 0), 'constant')[:len(out)]
           else:
               out[:] = 0

           return len(output_items[0])
   ```

3. **衛星鏈路預測**:
   ```python
   class SatelliteLinkPredictor:
       """預測未來的衛星鏈路參數"""
       def __init__(self, channel_model):
           self.channel_model = channel_model
           self.ts = load.timescale()

       def predict_next_n_seconds(self, duration_s, step_s=1.0):
           """預測未來 N 秒的鏈路參數"""
           t_now = self.ts.now()
           predictions = []

           for t_offset in np.arange(0, duration_s, step_s):
               t = self.ts.tt_jd(t_now.tt + t_offset / 86400)
               params = self.channel_model.compute_link_parameters(t)
               predictions.append({
                   'time_offset_s': t_offset,
                   **params
               })

           return predictions
   ```

#### 2.2 完整的 GNU Radio Flowgraph

```python
# ntn_sdr_transceiver.py
from gnuradio import gr, blocks, analog, digital, filter
from ntn_doppler_compensator import DopplerCompensator
from ntn_timing_advance import TimingAdvanceAdjuster
from ntn_channel_model import NTNChannelModel
from satellite_link_predictor import SatelliteLinkPredictor

class NTNSDRTransceiver(gr.top_block):
    """
    NTN SDR 收發器
    """
    def __init__(self, satellite_tle, ground_station):
        gr.top_block.__init__(self, "NTN SDR Transceiver")

        # 參數
        self.samp_rate = 10e6  # 10 MSPS
        self.center_freq = 12.5e9  # 12.5 GHz

        # NTN 通道模型
        self.channel_model = NTNChannelModel(
            satellite_tle,
            ground_station,
            12.5  # GHz
        )

        # 鏈路預測器
        self.link_predictor = SatelliteLinkPredictor(self.channel_model)

        # ==================== 發送鏈 ====================
        # 資料源（測試資料）
        self.data_source = blocks.vector_source_b(
            [i % 256 for i in range(10000)],
            True
        )

        # QPSK 調變
        self.modulator = digital.psk_mod(
            constellation_points=4,
            mod_code="gray",
            differential=False,
            samples_per_symbol=4,
            excess_bw=0.35
        )

        # Timing Advance
        self.tx_timing_advance = TimingAdvanceAdjuster(self.samp_rate)

        # ==================== 通道 ====================
        # NTN 通道（簡化：加入路徑損耗和都卜勒）
        self.channel_loss = blocks.multiply_const_cc(0.001)  # 路徑損耗

        # 都卜勒效應（頻率偏移）
        self.doppler_source = analog.sig_source_c(
            self.samp_rate,
            analog.GR_COS_WAVE,
            0,  # 初始頻率（將動態更新）
            1.0,
            0
        )
        self.doppler_mixer = blocks.multiply_cc()

        # 雜訊
        self.noise = analog.noise_source_c(
            analog.GR_GAUSSIAN,
            0.01,  # 標準差
            0
        )
        self.noise_adder = blocks.add_cc()

        # 傳播延遲
        self.propagation_delay = blocks.delay(
            gr.sizeof_gr_complex,
            int(0.004 * self.samp_rate)  # 4ms (LEO 典型延遲)
        )

        # ==================== 接收鏈 ====================
        # 都卜勒補償
        self.doppler_compensator = DopplerCompensator(
            self.samp_rate,
            self.center_freq
        )

        # Timing Advance 補償
        self.rx_timing_adjust = TimingAdvanceAdjuster(self.samp_rate)

        # QPSK 解調
        self.demodulator = digital.psk_demod(
            constellation_points=4,
            mod_code="gray",
            differential=False,
            samples_per_symbol=4,
            excess_bw=0.35
        )

        # Sink
        self.data_sink = blocks.vector_sink_b()

        # ==================== 連接 ====================
        # 發送
        self.connect(self.data_source, self.modulator)
        self.connect(self.modulator, self.tx_timing_advance)

        # 通道
        self.connect(self.tx_timing_advance, self.channel_loss)
        self.connect(self.channel_loss, (self.doppler_mixer, 0))
        self.connect(self.doppler_source, (self.doppler_mixer, 1))
        self.connect(self.doppler_mixer, (self.noise_adder, 0))
        self.connect(self.noise, (self.noise_adder, 1))
        self.connect(self.noise_adder, self.propagation_delay)

        # 接收
        self.connect(self.propagation_delay, self.doppler_compensator)
        self.connect(self.doppler_compensator, self.rx_timing_adjust)
        self.connect(self.rx_timing_adjust, self.demodulator)
        self.connect(self.demodulator, self.data_sink)

    def update_link_parameters(self):
        """根據衛星位置更新鏈路參數"""
        ts = load.timescale()
        t = ts.now()

        params = self.channel_model.compute_link_parameters(t)

        # 更新都卜勒頻移
        doppler_hz = params['doppler_shift_hz']
        self.doppler_source.set_frequency(doppler_hz)
        self.doppler_compensator.set_doppler_shift(doppler_hz)

        # 更新 Timing Advance
        delay_s = params['propagation_delay_s']
        self.tx_timing_advance.set_timing_advance(delay_s)

        # 更新路徑損耗
        loss_linear = 10 ** (-params['total_loss_db'] / 20)
        self.channel_loss.set_k(loss_linear)

        print(f"Updated link: Doppler={doppler_hz/1000:.2f} kHz, "
              f"Delay={delay_s*1000:.2f} ms, Loss={params['total_loss_db']:.1f} dB")

# 測試
if __name__ == '__main__':
    # LEO 衛星 TLE
    tle = (
        '1 43078U 17073A   23365.16928945  .00000000  00000-0  00000-0 0  9999',
        '2 43078  97.4000  59.5000 0001500  90.0000 270.0000 15.20000000    16'
    )

    # 台灣地面站
    station = ('25.0330 N', '121.5654 E')

    tb = NTNSDRTransceiver(tle, station)

    # 運行 10 秒，每秒更新鏈路參數
    import threading
    import time

    def update_loop():
        for _ in range(10):
            time.sleep(1)
            tb.update_link_parameters()

    tb.start()
    update_thread = threading.Thread(target=update_loop)
    update_thread.start()
    update_thread.join()
    tb.stop()
    tb.wait()

    # 檢查結果
    received = tb.data_sink.data()
    print(f"接收到 {len(received)} bytes")
```

#### 2.3 驗證標準
- [ ] GNU Radio flowgraph 成功運行
- [ ] 都卜勒補償正確實現
- [ ] Timing Advance 正確處理
- [ ] 可以模擬衛星移動的動態鏈路
- [ ] BER/PER 測量正確

---

**（續下一部分...）**

由於文檔過長，我將分為多個部分創建。這是第一部分，涵蓋了：
- 專案背景和 NTN 特殊需求
- 階段 0：環境準備
- 階段 1：NTN 通道模型
- 階段 2：GNU Radio 信號處理

請問我是否繼續創建後續階段（階段 3-6）？包括：
- 階段 3：ns-3 + ns-O-RAN 整合
- 階段 4：O-RAN RIC 和 xApp（考慮 NTN 特性）
- 階段 5：DRL 訓練（針對 NTN 優化）
- 階段 6：Kubernetes 部署和測試

或者您希望我先實際開始實施階段 0 和階段 1？
