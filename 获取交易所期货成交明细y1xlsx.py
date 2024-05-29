'''
这段代码将数据保存方式从csv改为xlsx。将以下代码的数据保存方式由csv改为xlsx，可以使用pandas库的to_excel方法。首先需要安装openpyxl库，然后修改save_deal_detail_to_csv函数。
'''
import os
import efinance as ef
import pandas as pd
from datetime import datetime

def save_deal_detail_to_excel(quote_id, max_count, file_name):
    try:
        # 获取期货最新交易日成交明细
        deal_detail = ef.futures.get_deal_detail(quote_id, max_count)

        # 处理重名文件，避免覆盖
        file_index = 1
        base_name, ext = os.path.splitext(file_name)
        while True:
            if not os.path.exists(file_name):
                deal_detail.to_excel(file_name, index=None)
                print(f'数据已保存到 {file_name}')
                break
            file_name = f"{base_name}_{file_index:02d}{ext}"
            file_index += 1

    except Exception as e:
        print(f"获取期货代码 {quote_id} 的成交明细数据失败：{str(e)}")

def main():
    # 获取当前本地日期
    local_date = datetime.now().strftime("%Y-%m-%d")

    # 生成保存数据的目录
    data_dir = f"./data/a/期货成交明细/{local_date}"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 从 code.txt 读取期货代码
    code_file_path = "code-list/期货行情id240425.txt"
    with open(code_file_path, "r") as file:
        futures_codes = [line.strip() for line in file]

    # 处理每个期货代码
    for futures_code in futures_codes:
        file_name = os.path.join(data_dir, f"{futures_code}.xlsx")
        save_deal_detail_to_excel(futures_code, 1000000, file_name)

if __name__ == "__main__":
    main()