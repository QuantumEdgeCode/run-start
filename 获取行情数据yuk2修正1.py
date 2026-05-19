# ============================================================
# 文件名称：获取行情数据yuk2修正1.py
# 功能描述：使用 yfinance 库批量获取全球股票市场历史行情数据
#          支持多市场、多时间周期配置，失败自动重试1次
#          数据按市场/周期/日期分类保存为CSV文件
# 原始脚本：单IP顺序下载（约3.5-4小时）
# 优化说明：配合20路并行工作流使用，按取模分配任务
# 作者：QuantumEdgecode & Deepseek-V4-Flash & 江城庄稼汉
# 更新时间：2024/06/18 16:00:08 GMT+08:00
# ============================================================

import yfinance as yf          # Yahoo Finance 数据接口库
import os                      # 操作系统接口，用于文件和目录操作
import logging                 # 日志记录模块，用于记录运行状态
import json                    # JSON 数据处理，用于读取市场配置文件
from datetime import datetime  # 日期时间处理，用于生成日期戳
import pandas as pd            # 数据分析库，yfinance 返回 DataFrame 格式
import time                    # 时间模块，用于请求间隔和重试等待


def get_current_date():
    """
    获取当前日期字符串
    
    返回:
        str: 格式为 'YYYY-MM-DD' 的当前日期，用于目录命名
    """
    return datetime.now().strftime('%Y-%m-%d')


def get_stock_data(ticker, period, interval):
    """
    获取单只股票的历史行情数据，失败时自动重试1次
    
    参数:
        ticker (str): 股票代码，如 'AAPL'、'0700.HK'
        period (str): 数据周期，如 '1d'、'1mo'、'1y'、'max'
        interval (str): 数据间隔，如 '1m'、'5m'、'1d'、'1wk'
    
    返回:
        pandas.DataFrame: 包含开盘价、最高价、最低价、收盘价、成交量的数据表
        None: 获取失败时返回空值
    
    重试机制:
        - 首次获取失败后，等待0.2秒自动重试1次
        - 两次都失败则记录错误日志并返回 None
    """
    max_retries = 1  # 最大重试次数：1次（总共最多尝试2次）
    
    for attempt in range(max_retries + 1):  # attempt 取值：0（首次）, 1（重试）
        try:
            # 创建 Ticker 对象，用于获取指定股票的数据
            stock = yf.Ticker(ticker)
            
            # 调用 history 方法获取历史行情数据
            # 返回 DataFrame，包含 Open、High、Low、Close、Volume 等列
            stock_df = stock.history(period=period, interval=interval)
            
            # 检查返回的数据是否为空（可能是股票代码错误或已退市）
            if stock_df.empty:
                raise ValueError(f"{ticker}: 无数据返回，可能已退市")
            
            # --- 数据获取成功 ---
            if attempt == 0:
                # 首次尝试就成功
                print(f"✓ {ticker} 获取成功")
            else:
                # 重试后成功
                print(f"✓ {ticker} 重试成功")
            
            return stock_df  # 返回股票数据
            
        except Exception as e:
            # --- 数据获取失败 ---
            if attempt < max_retries:
                # 首次尝试失败，还有重试机会
                print(f"⚠ {ticker} 首次失败，正在重试...")
                time.sleep(0.2)  # 等待0.2秒后重试，避免请求过快
            else:
                # 重试后仍然失败，记录错误
                print(f"✗ {ticker} 获取失败（已重试{max_retries}次）")
                logging.error(f"{ticker} 获取失败: {str(e)}")
    
    # 所有尝试都失败，返回 None
    return None


def setup_logging(log_dir, market):
    """
    设置日志记录系统
    
    参数:
        log_dir (str): 日志文件保存目录
        market (str): 市场名称，用于日志文件命名
    
    返回:
        logging.Logger: 配置好的日志记录器
    
    日志配置:
        - 文件日志：记录所有 INFO 及以上级别的信息到文件
        - 控制台日志：只显示 WARNING 及以上级别的信息
        - 日志文件命名格式：{market}_{日期}_log.txt
        - 避免重复添加处理器（handler）
    """
    current_date = get_current_date()
    log_file = os.path.join(log_dir, f"{market}_{current_date}_log.txt")

    # 创建日志记录器，以市场名称为标识
    logger = logging.getLogger(market)
    logger.setLevel(logging.INFO)  # 设置最低日志级别为 INFO

    # 文件处理器：将日志写入文件
    file_handler = logging.FileHandler(log_file, 'a', 'utf-8')  # 'a' 表示追加模式
    file_handler.setLevel(logging.INFO)

    # 控制台处理器：在终端显示日志
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)  # 控制台只显示警告及以上级别

    # 设置日志格式：时间 - 级别 - 消息内容
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 避免重复添加处理器（防止多次调用时日志重复输出）
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


def get_unique_filename(file_path):
    """
    生成唯一的文件名，防止文件被覆盖
    
    参数:
        file_path (str): 原始文件路径
    
    返回:
        str: 唯一的文件路径
    
    命名规则:
        - 如果文件不存在，直接返回原始路径
        - 如果文件已存在，在文件名后添加 _01、_02 等序号
        - 例如：AAPL.csv → AAPL_01.csv → AAPL_02.csv
    """
    # 检查文件是否已存在
    if not os.path.exists(file_path):
        return file_path
    
    # 分割文件名和扩展名
    filename, extension = os.path.splitext(file_path)
    
    # 从01开始递增序号，直到找到不存在的文件名
    index = 1
    while True:
        new_file_path = f"{filename}_{index:02d}{extension}"  # :02d 保证序号为两位数
        if not os.path.exists(new_file_path):
            return new_file_path
        index += 1


def write_data(df, code, directory, format):
    """
    将股票数据写入文件
    
    参数:
        df (pandas.DataFrame): 股票行情数据
        code (str): 股票代码，用作文件名
        directory (str): 保存目录路径
        format (str): 文件格式，如 'csv'
    
    返回:
        str: 实际保存的文件路径（可能是重命名后的唯一路径）
    
    功能:
        - 自动创建不存在的目录
        - 使用唯一文件名防止覆盖已有数据
        - 目前支持 CSV 格式（UTF-8 with BOM 编码，兼容 Excel）
    """
    # 创建目录（如果不存在），exist_ok=True 表示目录已存在也不报错
    try:
        os.makedirs(directory, exist_ok=True)
    except FileExistsError:
        pass  # 目录已存在，忽略错误
    
    # 构建完整文件路径
    filename = f"{directory}/{code}.{format}"
    
    # 获取唯一文件名（避免覆盖已有文件）
    unique_filename = get_unique_filename(filename)
    
    # 根据格式保存文件
    if format == 'csv':
        # encoding='utf-8-sig'：使用 UTF-8 with BOM 编码，Excel 可直接打开不乱码
        df.to_csv(unique_filename, encoding='utf-8-sig')
    
    return unique_filename


def load_market_data(file_path):
    """
    加载市场配置的 JSON 文件
    
    参数:
        file_path (str): JSON 配置文件路径
    
    返回:
        list: 按 id 排序的市场配置列表
    
    JSON 文件格式示例:
        [
            {
                "id": 1,
                "market": "HK",
                "file_name": "hk_stocks.txt",
                "interval": "1d",
                "period": "max",
                "save_format": "csv"
            }
        ]
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 按 id 排序，确保处理顺序一致
    return sorted(data, key=lambda x: x['id'])


def main():
    """
    主函数：批量获取股票数据并保存
    
    执行流程:
        1. 加载市场配置文件（markets-y2.json）
        2. 遍历每个市场配置
        3. 读取该市场的股票代码列表文件
        4. 逐只获取股票行情数据
        5. 保存数据到按市场/周期/日期分类的目录
        6. 记录成功/失败统计
        7. 市场间等待3秒，避免API限流
    """
    # ===== 第1步：加载市场配置 =====
    market_data = load_market_data('markets-y2.json')

    # ===== 第2步：遍历每个市场 =====
    for market_info in market_data:
        # 提取市场配置参数
        market = market_info['market']              # 市场代码，如 'HK'、'US'
        file_name = market_info['file_name']        # 股票列表文件名
        interval = market_info['interval']          # 数据间隔，如 '1d'、'1m'
        period = market_info['period']              # 数据周期，如 'max'、'1y'
        save_format = market_info['save_format']    # 保存格式，如 'csv'

        # ===== 特殊处理：1分钟线数据周期限制 =====
        # yfinance 限制：interval='1m' 时，period 最大只能为 '7d'
        if interval == "1m" and period == "max":
            print(f"警告：{market} 市场使用 interval='1m' 但 period='max'，已自动修正为 '7d'")
            period = "7d"

        # ===== 第3步：读取股票代码列表文件 =====
        current_date = get_current_date()
        
        # 先尝试在根目录查找文件
        file_path = f"./{file_name}"
        if not os.path.exists(file_path):
            # 如果根目录不存在，尝试在 yfcode-list 子目录查找
            file_path_in_code_list = f"./yfcode-list/{file_name}"
            if not os.path.exists(file_path_in_code_list):
                print(f"找不到文件: {file_name}，跳过此市场")
                continue
            file_path = file_path_in_code_list

        # 读取股票代码（跳过空行）
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tickers = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在，跳过此市场")
            continue

        # ===== 第4步：创建数据保存目录 =====
        # 目录结构：./data/{市场}/{间隔}/{日期}/
        # 例如：./data/HK/1d/2024-06-18/
        base_data_directory = f'./data/{market}/{interval}/{current_date}'
        os.makedirs(base_data_directory, exist_ok=True)
        
        # ===== 第5步：设置日志记录 =====
        logger = setup_logging(base_data_directory, market)
        logger.info(f"数据目录: {base_data_directory}")
        print(f"\n{'='*60}")
        print(f"数据目录: {base_data_directory}")
        print(f"开始处理 {market} 市场，共 {len(tickers)} 只股票")
        print(f"{'='*60}")

        # ===== 第6步：批量获取股票数据 =====
        success_count = 0  # 成功计数器
        fail_count = 0     # 失败计数器

        try:
            for ticker in tickers:
                # 获取单只股票数据
                stock_data = get_stock_data(ticker, period=period, interval=interval)
                
                if stock_data is not None:
                    # 获取成功，保存数据
                    saved_file = write_data(stock_data, ticker, base_data_directory, save_format)
                    logger.info(f"{ticker} 的数据成功保存到 {saved_file}")
                    success_count += 1
                else:
                    # 获取失败
                    logger.error(f"未能检索 {ticker} 的数据")
                    fail_count += 1
                
                # 每只股票之间等待0.2秒，避免请求频率过高被限流
                time.sleep(0.2)
            
            # ===== 第7步：输出市场处理结果 =====
            print(f"\n{market} 市场处理完成：成功 {success_count} 只，失败 {fail_count} 只")
            
            # 市场间等待3秒，给 API 服务器缓冲时间
            time.sleep(3)
            
        except KeyboardInterrupt:
            # 用户手动中断（Ctrl+C）
            logger.warning("数据获取过程被中断")
            print("\n数据获取过程被中断")
            break


# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    """
    当脚本直接运行时执行 main() 函数
    当脚本被 import 导入时，不自动执行（供20路并行工作流调用）
    """
    main()
