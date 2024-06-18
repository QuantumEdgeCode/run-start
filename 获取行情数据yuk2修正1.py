#2024/06/18 16:00:08 GMT+08:00
import yfinance as yf
import os
import logging
import json
from datetime import datetime
import pandas as pd
from requests import Session
import time

# 初始化会话
session = Session()
session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

def get_current_date():
    """获取当前日期"""
    return datetime.now().strftime('%Y-%m-%d')

def get_stock_data(ticker, period, interval):
    """获取股票数据，失败时重试一次"""
    for attempt in range(1):  # 尝试1次
        try:
            stock = yf.Ticker(ticker, session=session)  # 使用会话
            stock_df = stock.history(period=period, interval=interval)
            if stock_df.empty:
                raise ValueError(f"{ticker}: No data found, symbol may be delisted")
            return stock_df
        except Exception as e:
            error_message = f"尝试获取 {ticker} 数据失败，尝试次数：{attempt + 1}。错误信息：{str(e)}"
            logging.error(error_message)
            print(error_message)
    return None

def setup_logging(log_dir, market):
    """设置日志记录"""
    current_date = get_current_date()
    log_file = os.path.join(log_dir, f"{market}_{current_date}_log.txt")

    # 获取或创建一个新的日志记录器
    logger = logging.getLogger(market)
    logger.setLevel(logging.INFO)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, 'a', 'utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建流处理器
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)  # 设置为WARNING，以减少控制台输出

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 如果日志记录器没有处理器，则添加处理器
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
        pass  # 目录已经存在，忽略该错误
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

    # 遍历市场数据
    for market_info in market_data:
        market = market_info['market']
        file_name = market_info['file_name']
        interval = market_info['interval']
        period = market_info['period']
        save_format = market_info['save_format']

        # 读取文件路径
        current_date = get_current_date()
        file_path = f"./{file_name}"
        if not os.path.exists(file_path):
            file_path_in_code_list = f"./yfcode-list/{file_name}"
            if not os.path.exists(file_path_in_code_list):
                print(f"找不到文件: {file_name}，跳过此市场")
                continue
            file_path = file_path_in_code_list

        # 读取股票代码
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tickers = [line.strip() for line in file]
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在，跳过此市场")
            continue

        # 设置数据目录和日志目录
        base_data_directory = f'./data/{market}/{interval}/{current_date}'
        os.makedirs(base_data_directory, exist_ok=True)
        
        # 设置日志记录器
        logger = setup_logging(base_data_directory, market)
        logger.info(f"数据目录: {base_data_directory}")
        print(f"数据目录: {base_data_directory}")  # 控制台输出数据目录

        # 获取数据并保存
        try:
            for ticker in tickers:
                stock_data = get_stock_data(ticker, period=period, interval=interval)
                if stock_data is not None:
                    saved_file = write_data(stock_data, ticker, base_data_directory, save_format)
                    logger.info(f"{ticker} 的数据成功保存到 {saved_file}")
                    print(f"{ticker} 的数据成功保存到 {saved_file}")  # 控制台输出保存文件信息
                else:
                    error_message = f"未能检索 {ticker} 的数据"
                    logger.error(error_message)
            time.sleep(5)  # 每个市场数据处理完后等待5秒
        except KeyboardInterrupt:
            logger.warning("数据获取过程被中断")
            print("数据获取过程被中断")  # 控制台输出中断信息
            break

if __name__ == "__main__":
    main()
