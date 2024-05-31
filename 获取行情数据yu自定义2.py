#2024/05/30 10:36:22 GMT+08:00
import yfinance as yf
import os
import logging
from datetime import datetime
import pandas as pd
from requests import Session

# 初始化会话
session = Session()
session.headers['User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'

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

def get_log_file_path(log_dir):
    """获取日志文件路径，确保文件名唯一"""
    current_date = get_current_date()
    base_log_file = os.path.join(log_dir, f"{current_date}_log.txt")
    if not os.path.exists(base_log_file):
        return base_log_file
    i = 1
    while True:
        log_file = os.path.join(log_dir, f"{current_date}_log_{i:02d}.txt")
        if not os.path.exists(log_file):
            return log_file
        i += 1

def setup_logging(log_dir):
    """设置日志记录"""
    log_file = get_log_file_path(log_dir)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, 'a', 'utf-8'),
            logging.StreamHandler()
        ]
    )

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

def main():
    """主函数，获取股票数据并保存"""
    # 硬编码的参数
    file_name = 'test.txt'
    market = 'us'
    interval = '1m'
    period = 'max'  # yfinance限制1分钟级别的最大周期为7天
    save_format = 'csv'

    # 读取文件路径
    current_date = get_current_date()
    file_path = f"./{file_name}"
    if not os.path.exists(file_path):
        file_path_in_code_list = f"./yfcode-list/{file_name}"
        if not os.path.exists(file_path_in_code_list):
            raise FileNotFoundError(f"找不到文件: {file_name}")
        file_path = file_path_in_code_list

    # 读取股票代码
    with open(file_path, "r", encoding="utf-8") as file:
        tickers = [line.strip() for line in file]

    # 设置数据目录
    base_data_directory = f'./data/{market}/{interval}/{current_date}'
    os.makedirs(base_data_directory, exist_ok=True)
    setup_logging(base_data_directory)
    print(f"数据目录: {base_data_directory}")

    # 获取数据并保存
    try:
        for ticker in tickers:
            stock_data = get_stock_data(ticker, period=period, interval=interval)
            if stock_data is not None:
                saved_file = write_data(stock_data, ticker, base_data_directory, save_format)
                print(f"{ticker} 的数据成功保存到 {saved_file}")
                logging.info(f"{ticker} 的数据成功保存到 {saved_file}")
            else:
                error_message = f"未能检索 {ticker} 的数据"
                logging.error(error_message)
    except KeyboardInterrupt:
        print("数据获取过程被中断")
        logging.warning("数据获取过程被中断")

if __name__ == "__main__":
    main()
