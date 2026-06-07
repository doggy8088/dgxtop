# DGXTOP for The DGX SPARK

[English](#dgxtop-for-the-dgx-spark) | [繁體中文](#dgxtop-for-the-dgx-spark-繁體中文說明)

A performance monitoring CLI tool for Ubuntu inspired by asitop for Mac, with added volume transfer speed monitoring capabilities.

<img width="1623" height="928" alt="image" src="https://github.com/user-attachments/assets/04be8850-617c-4af0-8f1d-4a369cb8e7c2" />


## Features

- **Volume Transfer Speed Monitoring**: Real-time read/write speed tracking per drive
- **System Monitoring**: GB10 GPU, CPU, memory, and network statistics
- **Real-time Display**: Interactive terminal interface with customizable update intervals
- **Lightweight**: Minimal dependencies, uses native Linux `/proc` filesystem
- **Per-Drive Performance**: Detailed breakdown of I/O performance for each storage device

## Installation

Install using the one-line installer script:

```bash
curl -sSL https://raw.githubusercontent.com/doggy8088/dgxtop/main/install.sh | bash
```

Alternatively, you can manually download and install the `.deb` package to `/tmp` (to avoid sandbox permission warnings):

```bash
cd /tmp
wget https://github.com/doggy8088/dgxtop/releases/latest/download/dgxtop_1.0.0-1_all.deb
sudo apt install ./dgxtop_1.0.0-1_all.deb
```

That's it. Dependencies are installed automatically.

## Usage

### Basic Usage

```bash
dgxtop
```

### Options

```bash
dgxtop --interval 0.5        # Update every 0.5 seconds
dgxtop -i 2.0              # Update every 2 seconds
dgxtop --version           # Show version information
```

### Interactive Controls

- `q` - Quit the application
- `+` - Speed up update interval
- `-` - Slow down update interval

## Architecture

```
dgxtop/
├── __init__.py          # Package initialization
├── main.py             # Main application entry point
├── disk_monitor.py     # Disk I/O monitoring (/proc/diskstats)
├── system_monitor.py   # CPU, memory, network monitoring
├── gpu_monitor.py      # GPU monitoring (nvidia-smi)
└── display_manager.py  # Terminal UI management
```

## Technical Details

### Volume Transfer Speed Calculation

The tool calculates transfer speeds by reading `/proc/diskstats` at regular intervals:

```
Read/Write Bytes per Second = (Δsectors) × 512 bytes / Δtime
```

Where:
- `Δsectors` = Difference in sectors read/written between measurements
- `512 bytes` = Standard sector size in Linux
- `Δtime` = Time interval between measurements

### Data Sources

- **Disk Statistics**: `/proc/diskstats`
- **CPU Statistics**: `/proc/stat`
- **Memory Statistics**: `/proc/meminfo`
- **Network Statistics**: `/proc/net/dev`
- **GPU Statistics**:  `nvidia-smi`

## Requirements

- Python 3.8+
- DGX Spark with NVidia Ubuntu 
- curses (usually included with Python)

## Building from Source

### On Ubuntu

```bash
git clone https://github.com/doggy8088/dgxtop.git
cd dgxtop

sudo apt install debhelper dh-python python3-all python3-setuptools dpkg-dev
dpkg-buildpackage -us -uc -b

sudo apt install ../dgxtop_1.0.0-1_all.deb
```

### On macOS (using Docker)

```bash
git clone https://github.com/doggy8088/dgxtop.git
cd dgxtop

docker run --rm -v "$(pwd)":/workspace ubuntu:24.04 bash -c "
  apt-get update > /dev/null 2>&1 &&
  apt-get install -y debhelper dh-python python3-all python3-setuptools dpkg-dev > /dev/null 2>&1 &&
  mkdir -p /tmp/build_area/dgxtop && cp -r /workspace/* /tmp/build_area/dgxtop/ 2>/dev/null || true &&
  cd /tmp/build_area/dgxtop && dpkg-buildpackage -us -uc -b &&
  mkdir -p /workspace/deb_build && cp /tmp/build_area/*.deb /workspace/deb_build/
"

# Output: deb_build/dgxtop_1.0.0-1_all.deb
```

## License

APACHE 2.0 License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Differences from asitop for Mac

While inspired by the original asitop for Mac, this DGX Spark version:

- Uses Linux's `/proc` filesystem instead of macOS `powermetrics`
- Focuses on volume transfer speed monitoring per drive
- Provides a more generalized system monitoring approach

## Roadmap

- [ ] Add process monitoring
- [ ] Implement alerting thresholds
- [ ] Add configuration file support
- [ ] Create systemd service option
- [ ] Add network interface specific monitoring
- [ ] Implement logging functionality

---

# DGXTOP for The DGX SPARK (繁體中文說明)

專為 Ubuntu 設計的效能監控 CLI 工具，靈感來自 Mac 的 asitop，並新增了硬碟磁碟傳輸速度監控功能。

<img width="1623" height="928" alt="image" src="https://github.com/user-attachments/assets/04be8850-617c-4af0-8f1d-4a369cb8e7c2" />


## 功能特點

- **磁碟傳輸速度監控**：即時追蹤每個硬碟的讀取/寫入速度
- **系統監控**：GB10 GPU、CPU、記憶體及網路統計數據
- **即時顯示**：互動式終端介面，支援自訂更新頻率
- **輕量級**：極簡相依性，使用 Linux 原生的 `/proc` 檔案系統
- **單一硬碟效能**：詳細拆解每個儲存裝置的 I/O 效能

## 安裝

使用一鍵安裝指令檔進行安裝：

```bash
curl -sSL https://raw.githubusercontent.com/doggy8088/dgxtop/main/install.sh | bash
```

或者，您也可以手動下載並將 `.deb` 套件安裝至 `/tmp` 目錄（以避免沙箱權限警告）：

```bash
cd /tmp
wget https://github.com/doggy8088/dgxtop/releases/latest/download/dgxtop_1.0.0-1_all.deb
sudo apt install ./dgxtop_1.0.0-1_all.deb
```

就這麼簡單。所有相依套件皆會自動安裝。

## 使用方法

### 基本用法

```bash
dgxtop
```

### 參數選項

```bash
dgxtop --interval 0.5        # 每 0.5 秒更新一次
dgxtop -i 2.0              # 每 2 秒更新一次
dgxtop --version           # 顯示版本資訊
```

### 互動式控制

- `q` - 結束應用程式
- `+` - 加快更新頻率
- `-` - 減慢更新頻率

## 架構

```
dgxtop/
├── __init__.py          # 套件初始化
├── main.py             # 主應用程式入口點
├── disk_monitor.py     # 磁碟 I/O 監控 (/proc/diskstats)
├── system_monitor.py   # CPU、記憶體、網路監控
├── gpu_monitor.py      # GPU 監控 (nvidia-smi)
└── display_manager.py  # 終端機 UI 管理
```

## 技術細節

### 磁碟傳輸速度計算方式

此工具透過定期讀取 `/proc/diskstats` 來計算傳輸速度：

```
每秒讀取/寫入位元組 = (Δsectors) × 512 位元組 / Δtime
```

其中：
- `Δsectors` = 兩次測量之間讀取/寫入的磁區差值
- `512 bytes` = Linux 中的標準磁區大小
- `Δtime` = 測量之間的時間間隔

### 數據來源

- **磁碟統計**：`/proc/diskstats`
- **CPU 統計**：`/proc/stat`
- **記憶體統計**：`/proc/meminfo`
- **網路統計**：`/proc/net/dev`
- **GPU 統計**：`nvidia-smi`

## 系統需求

- Python 3.8+
- 搭載 NVIDIA Ubuntu 的 DGX Spark
- curses（通常隨 Python 內建）

## 從原始碼建置

### 在 Ubuntu 上

```bash
git clone https://github.com/doggy8088/dgxtop.git
cd dgxtop

sudo apt install debhelper dh-python python3-all python3-setuptools dpkg-dev
dpkg-buildpackage -us -uc -b

sudo apt install ../dgxtop_1.0.0-1_all.deb
```

### 在 macOS 上 (使用 Docker)

```bash
git clone https://github.com/doggy8088/dgxtop.git
cd dgxtop

docker run --rm -v "$(pwd)":/workspace ubuntu:24.04 bash -c "
  apt-get update > /dev/null 2>&1 &&
  apt-get install -y debhelper dh-python python3-all python3-setuptools dpkg-dev > /dev/null 2>&1 &&
  mkdir -p /tmp/build_area/dgxtop && cp -r /workspace/* /tmp/build_area/dgxtop/ 2>/dev/null || true &&
  cd /tmp/build_area/dgxtop && dpkg-buildpackage -us -uc -b &&
  mkdir -p /workspace/deb_build && cp /tmp/build_area/*.deb /workspace/deb_build/
"

# 輸出結果: deb_build/dgxtop_1.0.0-1_all.deb
```

## 授權條款

APACHE 2.0 授權條款 - 詳見 LICENSE 檔案。

## 貢獻

1. Fork 本儲存庫
2. 建立您的特性分支 (feature branch)
3. 進行修改
4. 新增相關測試（如適用）
5. 送出 Pull Request

## 與 Mac 版 asitop 的差異

雖然靈感來自 Mac 原版的 asitop，但此 DGX Spark 版本：

- 使用 Linux 的 `/proc` 檔案系統而非 macOS 的 `powermetrics`
- 著重於監控每個硬碟的磁碟傳輸速度
- 提供更通用的系統監控方法

## 開發路線圖

- [ ] 新增行程監控 (Process monitoring)
- [ ] 實作警告閾值
- [ ] 新增設定檔支援
- [ ] 建立 systemd 服務選項
- [ ] 新增特定網路介面的監控
- [ ] 實作日誌記錄功能
