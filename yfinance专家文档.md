# yfinance 股票数据采集系统 - 使用文档

> 作者：QuantumEdgecode & Deepseek-V4-Flash & 江城庄稼汉  
> 文档生成日期：2026-05-19

---

## 项目概述

基于 yfinance 库的全球股票市场历史行情数据批量采集系统。

- 原始模式：单IP顺序下载，耗时约 3.5-4 小时
- 并行模式：20路并行下载，耗时约 10-15 分钟
- 数据来源：Yahoo Finance
- 支持市场：港股、美股、A股、加密货币等多个市场
- 数据格式：CSV（UTF-8 with BOM 编码，Excel 可直接打开）


## 项目文件结构

    项目根目录/
    │
    ├── .github/workflows/
    │   ├── 09.yml                              # 单线程工作流（原始版）
    │   └── 10.yml                              # 20路并行工作流（优化版）
    │
    ├── 获取行情数据yuk2修正1.py                 # 核心数据采集脚本
    ├── markets-y2.json                         # 市场配置文件
    │
    ├── yfcode-list/                            # 股票代码列表目录
    │   ├── hk_stocks.txt                       # 港股代码列表
    │   ├── us_stocks.txt                       # 美股代码列表
    │   └── ...                                 # 其他市场代码列表
    │
    ├── data/                                   # 数据输出目录（自动生成）
    │   └── {市场}/{间隔}/{日期}/
    │       └── {股票代码}.csv
    │
    └── logs/                                   # 日志输出目录（自动生成）
        └── {市场}_{日期}_log.txt


## 核心文件说明

### 1. 获取行情数据yuk2修正1.py

主数据采集脚本，包含以下核心函数：

#### get_current_date()
获取当前日期字符串。

返回值：str，格式 'YYYY-MM-DD'

#### get_stock_data(ticker, period, interval)
获取单只股票的历史行情数据，失败时自动重试1次。

参数：
- ticker (str)：股票代码，如 'AAPL'、'0700.HK'
- period (str)：数据周期，如 '1d'、'1mo'、'1y'、'max'
- interval (str)：数据间隔，如 '1m'、'5m'、'1d'、'1wk'

返回值：
- pandas.DataFrame：包含 Open、High、Low、Close、Volume 列
- None：获取失败时返回空值

重试机制：
- 首次获取失败后，等待0.5秒自动重试1次
- 两次都失败则记录错误日志并返回 None

控制台输出示例：
- 首次成功：✓ AAPL 获取成功
- 重试成功：⚠ AAPL 首次失败，正在重试... → ✓ AAPL 重试成功
- 最终失败：⚠ AAPL 首次失败，正在重试... → ✗ AAPL 获取失败（已重试1次）

#### setup_logging(log_dir, market)
设置日志记录系统。

参数：
- log_dir (str)：日志文件保存目录
- market (str)：市场名称，用于日志文件命名

日志配置：
- 文件日志：记录所有 INFO 及以上级别
- 控制台日志：只显示 WARNING 及以上级别
- 日志文件命名格式：{market}_{日期}_log.txt

#### get_unique_filename(file_path)
生成唯一文件名，防止文件覆盖。

参数：
- file_path (str)：原始文件路径

命名规则：
- 文件不存在：直接返回原始路径
- 文件已存在：添加 _01、_02 等序号
- 示例：AAPL.csv → AAPL_01.csv → AAPL_02.csv

#### write_data(df, code, directory, format)
将股票数据写入CSV文件。

参数：
- df (pandas.DataFrame)：股票行情数据
- code (str)：股票代码，用作文件名
- directory (str)：保存目录路径
- format (str)：文件格式，如 'csv'

编码：UTF-8 with BOM，Excel 可直接打开

#### load_market_data(file_path)
加载市场配置的 JSON 文件。

参数：
- file_path (str)：JSON 配置文件路径

返回值：list，按 id 排序的市场配置列表

#### main()
主函数，执行完整的批量数据采集流程。

执行流程：
1. 加载市场配置文件
2. 遍历每个市场配置
3. 读取股票代码列表文件
4. 逐只获取股票行情数据
5. 保存到按市场/周期/日期分类的目录
6. 记录成功/失败统计
7. 市场间等待3秒，避免API限流


### 2. markets-y2.json

市场配置文件，定义需要采集的市场参数。

格式示例：
[
    {
        "id": 1,
        "market": "HK",
        "file_name": "hk_stocks.txt",
        "interval": "1d",
        "period": "max",
        "save_format": "csv"
    },
    {
        "id": 2,
        "market": "US",
        "file_name": "us_stocks.txt",
        "interval": "1d",
        "period": "max",
        "save_format": "csv"
    }
]

字段说明：
- id：市场序号，决定处理顺序
- market：市场代码，用于目录命名
- file_name：股票代码列表文件名
- interval：K线间隔（1m/5m/15m/30m/1h/1d/1wk/1mo）
- period：数据周期（1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max）
- save_format：保存格式（csv）

注意事项：
- 1分钟线（interval='1m'）的 period 最大为 '7d'，脚本会自动修正
- 股票代码列表文件优先在根目录查找，其次在 yfcode-list/ 子目录查找


### 3. 股票代码列表文件

每行一个股票代码，支持 yfinance 格式。

港股示例（hk_stocks.txt）：
0700.HK
9988.HK
0005.HK
0388.HK

美股示例（us_stocks.txt）：
AAPL
GOOGL
MSFT
TSLA

A股示例（cn_stocks.txt）：
600036.SS
000858.SZ

加密货币示例（crypto_stocks.txt）：
BTC-USD
ETH-USD


## GitHub Actions 工作流

### 09.yml - 单线程模式

触发方式：
- 手动触发（workflow_dispatch）
- 定时触发：每周六北京时间 09:00（cron: '0 1 * * 6'）

执行流程：
1. 环境准备（Python 3.11 + 依赖安装）
2. 生成版本号（格式：vYYYYMMDD-运行编号）
3. 运行数据采集脚本
4. 打包数据文件（stock_data_版本号.zip）
5. 打包日志文件（workflow_logs_版本号.zip）
6. 创建 GitHub Release 并上传附件
7. 发送邮件通知（含数据统计、节点IP、Release链接）
8. 清理临时文件

预计耗时：3.5-4 小时


### 10.yml - 20路并行模式

触发方式：同 09.yml

三阶段流水线架构：

阶段1：split-tasks（任务拆分）
- 读取 markets-y2.json 统计总任务数
- 输出 20 个 Worker 编号

阶段2：download-worker（并行下载）
- 20 个并行 Job，每个使用独立 IP
- 任务分配：按 index % 20 取模
- 每个 Worker 独立运行获取行情数据yuk2修正1.py 核心函数
- 数据上传为独立 Artifact（保留1天）

阶段3：merge-and-release（合并发布）
- 下载所有 Worker 的 Artifact 并合并
- 收集 20 个节点的 IP 地址和统计信息
- 打包数据文件（stock_data_版本号.zip）
- 打包日志文件（workflow_logs_版本号.zip）
- 创建 GitHub Release 并上传附件
- 发送邮件通知（含20节点IP、统计卡片、Release链接）
- 清理临时文件

预计耗时：10-15 分钟


## 环境依赖

### Python 版本
Python 3.11+

### Python 库
- yfinance：Yahoo Finance 数据接口
- pandas：数据处理和分析
- openpyxl：Excel 文件支持（可选）
- curl_cffi：网络请求支持（可选，用于绕过反爬）

安装命令：
pip install yfinance pandas openpyxl curl_cffi

### 系统工具（仅 GitHub Actions 需要）
- jq：JSON 处理工具
- zip：文件压缩工具

安装命令：
sudo apt-get install -y jq zip


## 配置 Secrets（邮件通知）

在 GitHub 仓库 Settings → Secrets and variables → Actions 中配置：

MAIL_ADDRESS：邮件服务器地址（如 smtp.gmail.com）
MAIL_PORT：邮件服务器端口（如 587）
MAIL_USERNAME：邮件账号
MAIL_PASSWORD：邮件密码或应用专用密码
MAIL_TO：接收通知的邮箱地址


## 数据目录结构

```
data/
├── HK/                         # 港股数据
│   ├── 1d/                     # 日线数据
│   │   └── 2024-06-18/         # 采集日期
│   │       ├── 0700.HK.csv     # 腾讯控股
│   │       ├── 9988.HK.csv     # 阿里巴巴
│   │       └── ...
│   ├── 1m/                     # 1分钟线数据
│   │   └── 2024-06-18/
│   │       └── ...
│   └── 1wk/                    # 周线数据
│       └── ...
│
├── US/                         # 美股数据
│   ├── 1d/
│   │   └── 2024-06-18/
│   │       ├── AAPL.csv
│   │       ├── GOOGL.csv
│   │       └── ...
│   └── ...
│
└── CRYPTO/                     # 加密货币数据
    └── ...
```


## CSV 数据格式

每只股票的 CSV 文件包含以下列：

| 列名 | 说明 |
|------|------|
| Date | 日期时间（索引列） |
| Open | 开盘价 |
| High | 最高价 |
| Low | 最低价 |
| Close | 收盘价 |
| Volume | 成交量 |
| Dividends | 股息（如有） |
| Stock Splits | 股票拆分（如有） |


## 常见问题

### Q1：为什么 1分钟线数据只有最近7天？
A：yfinance API 限制，interval='1m' 时 period 最大为 '7d'。脚本会自动将 'max' 修正为 '7d'。

### Q2：为什么有些股票获取失败？
A：可能原因：
- 股票已退市或代码错误
- Yahoo Finance API 限流
- 网络连接问题
脚本会自动重试1次，仍失败则跳过并记录日志。

### Q3：并行模式为什么比单线程快这么多？
A：20个独立IP同时下载，每个Worker只处理 1/20 的任务量，大幅减少等待时间。

### Q4：数据会保存多久？
A：GitHub Release 中的附件永久保存，不占用仓库 LFS 配额。Worker 的临时 Artifact 仅保留1天。

### Q5：如何添加新市场？
A：
1. 在 yfcode-list/ 目录创建股票代码列表文件
2. 在 markets-y2.json 中添加市场配置
3. 下次工作流运行时会自动包含新市场


## 版本历史

v1.0 (2024-06-18)
- 初始版本
- 支持单线程顺序下载
- 自动创建 Release 和邮件通知

v2.0 (2026-05-18)
- 新增20路并行下载模式
- 按取模分配任务，每个Worker使用独立IP
- 预计耗时从3.5-4小时降至10-15分钟
- 修复重试次数显示不准确问题
- 优化控制台输出信息


## 技术架构

单线程模式：
用户触发 → 单节点运行脚本 → 打包数据 → 创建Release → 发送邮件

并行模式：
用户触发 → 拆分任务 → 20节点并行下载 → 合并数据 → 创建Release → 发送邮件
         ↓                    ↓                    ↓
    split-tasks        download-worker      merge-and-release
    (1个Job)           (20个并行Job)         (1个Job)


## 许可证
开源使用项目
