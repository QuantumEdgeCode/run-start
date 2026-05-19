#2024/06/18 16:00:08 GMT+08:00
import yfinance as yf
import os
import logging
import json
from datetime import datetime
import pandas as pd
import time

def get_current_date():
    """获取当前日期"""
    return datetime.now().strftime('%Y-%m-%d')

def get_stock_data(ticker, period, interval):
    """获取股票数据，失败时重试1次"""
    max_attempts = 2  # 总共2次尝试（首次 + 1次重试）
    
    for attempt in range(max_attempts):
        try:
            stock = yf.Ticker(ticker)
            stock_df = stock.history(period=period, interval=interval)
            
            if stock_df.empty:
                raise ValueError(f"{ticker}: No data found, symbol may be delisted")
            return stock_df
            
        except Exception as e:
            error_message = f"尝试获取 {ticker} 数据失败，尝试次数：{attempt + 1}/{max_attempts}。错误信息：{str(e)}"
            logging.error(error_message)
            print(error_message)
            
            if attempt < max_attempts - 1:  # 如果不是最后一次尝试
                time.sleep(0.2)  # 等待0.2秒后重试
    return None

def setup_logging(log_dir, market):
    """设置日志记录"""
    current_date = get_current_date()
    log_file = os.path.join(log_dir, f"{market}_{current_date}_log.txt")

    logger = logging.getLogger(market)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file, 'a', 'utf-8')
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

def get_unique_filename(file_path):
    """获取唯一的文件名，防止文件覆盖"""
    if not os.path.exists(file_path):
        return file_path
    filename, extension = os.path.splitext(file_path)
    index = 1
    while True:
        new_file_path = f"{filename}_{index:02d}{extension}"
        if not os.path.exists(new_file_path):
            return new_file_path
        index += 1

def write_data(df, code, directory, format):
    """将数据写入文件"""
    try:
        os.makedirs(directory, exist_ok=True)
    except FileExistsError:
        pass
    filename = f"{directory}/{code}.{format}"
    unique_filename = get_unique_filename(filename)
    if format == 'csv':
        df.to_csv(unique_filename, encoding='utf-8-sig')
    return unique_filename

def load_market_data(file_path):
    """加载市场数据的JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return sorted(data, key=lambda x: x['id'])

def main():
    """主函数，获取股票数据并保存"""
    # 加载市场数据
    market_data = load_market_data('markets-y2.json')

    for market_info in market_data:
        market = market_info['market']
        file_name = market_info['file_name']
        interval = market_info['interval']
        period = market_info['period']
        save_format = market_info['save_format']

        # ===== 建议修复：1分钟线数据 period 不能超过 "7d" =====
        if interval == "1m" and period == "max":
            print(f"警告：{market} 市场使用 interval='1m' 但 period='max'，已自动修正为 '7d'")
            period = "7d"

        current_date = get_current_date()
        file_path = f"./{file_name}"
        if not os.path.exists(file_path):
            file_path_in_code_list = f"./yfcode-list/{file_name}"
            if not os.path.exists(file_path_in_code_list):
                print(f"找不到文件: {file_name}，跳过此市场")
                continue
            file_path = file_path_in_code_list

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tickers = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在，跳过此市场")
            continue

        base_data_directory = f'./data/{market}/{interval}/{current_date}'
        os.makedirs(base_data_directory, exist_ok=True)
        
        logger = setup_logging(base_data_directory, market)
        logger.info(f"数据目录: {base_data_directory}")
        print(f"数据目录: {base_data_directory}")
        print(f"开始处理 {market} 市场，共 {len(tickers)} 只股票")

        success_count = 0
        fail_count = 0

        try:
            for ticker in tickers:
                stock_data = get_stock_data(ticker, period=period, interval=interval)
                if stock_data is not None:
                    saved_file = write_data(stock_data, ticker, base_data_directory, save_format)
                    logger.info(f"{ticker} 的数据成功保存到 {saved_file}")
                    print(f"✓ {ticker} 保存成功")
                    success_count += 1
                else:
                    logger.error(f"未能检索 {ticker} 的数据")
                    print(f"✗ {ticker} 获取失败")
                    fail_count += 1
                
                # 每个股票之间短暂等待，避免请求过快
                time.sleep(0.2)
            
            print(f"\n{market} 市场处理完成：成功 {success_count} 只，失败 {fail_count} 只")
            time.sleep(3)  # 市场间等待
            
        except KeyboardInterrupt:
            logger.warning("数据获取过程被中断")
            print("\n数据获取过程被中断")
            break

if __name__ == "__main__":
    main()
