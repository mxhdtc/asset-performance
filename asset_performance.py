#coding = utf-8
import pandas as pd
import  numpy as np
from dateutil.relativedelta import relativedelta
import os
import matplotlib.pyplot as plt
import calendar
from math import *

#参数设置
init_asset = 1#初识资产的净值
start_time = '2013-01-01'  # 起始时间，输入格式为YYYY-MM-DD
end_time = '2020-05-31'  # 结束时间，输入格式为YYYY-MM-DD
path = '/Users/maxiaohang/指数数据/'  # 资产数据存放的文件夹路径
path_macro = '/Users/maxiaohang/宏观数据.xlsx'  # 宏观数据的存放路径
path_rate = '/Users/maxiaohang/利率数据.xlsx'  # 利率数据的存放路径
asset_num = 12


class asset_performance():
    def __init__(self, asset_payoff, asset_name, signal_payoff, start_time=start_time, end_time=end_time):
        #asset_payoff 资产的月频收益率数据
        #asset_name 基金的名称
        #signal_payoff 用于构造信号的资产的,需要提前计算好
        self.start_time = start_time
        self.end_time = end_time
        self.asset_payoff = asset_payoff
        self.signal_payoff = signal_payoff
        self.asset_name = asset_name


    def rate_liquidity_signal(self, month, monthly_payoff):
        #按照1年期国债、10年期国债、1年期信用债均线方法给出流动性信号(利率表征)
        #当月收益率小于均线视为宽松
        # monthly_payoff是月收益率，其索引为每月的最后一天
        # month为当月最后一天
        month = pd.to_datetime(month)
        mean_payoff = monthly_payoff[(monthly_payoff.index > month - relativedelta(months=12)) &
                                      (monthly_payoff.index < month + relativedelta(months=1))].mean()
        month_payoff = monthly_payoff.loc[month]
        flag = 0
        for i in mean_payoff.index:
            if mean_payoff.loc[i] > month_payoff.loc[i]:
                flag = flag + 1
        return flag/len(mean_payoff.index) > 2.0/3.0

    def asset_performance(self):
        asset_payoff = self.asset_payoff[(self.asset_payoff.index >= self.start_time) &
                        (self.asset_payoff.index <= self.end_time)]
        index = asset_payoff.resample('M').apply(lambda x: x[-1]).index#取每月最后一天
        currency_strong = 0
        currency_strong_up = 0
        currency_strong_paypff = 0
        currency_weak = 0
        currency_weak_up = 0
        currency_weak_payoff = 0
        for month in index:
            if self.rate_liquidity_signal(month, self.signal_payoff):#判断当月为货币宽松
                currency_strong = currency_strong + 1
                currency_strong_paypff = currency_strong_paypff + asset_payoff.loc[month]
                if asset_payoff.loc[month] > 0:
                    currency_strong_up = currency_strong_up +1
            else:#判断为货币紧缩
                currency_weak = currency_weak + 1
                currency_weak_payoff = currency_weak_payoff + asset_payoff.loc[month]
                if asset_payoff.loc[month] > 0:
                    currency_weak_up = currency_weak_up + 1
        return currency_strong_paypff/currency_strong, currency_strong_up/currency_strong, \
               currency_weak_payoff/currency_weak, currency_weak_up/currency_weak



def get_file_name(path, filetype):#读取文件的名字
    file_name = []
    os.chdir(path)
    for root, dir, files in os.walk(os.getcwd()):
        for file in files:
            if os.path.splitext(file)[1] in filetype:
                # print(os.path.splitext(file)[1])
                file_name.append(file)
    return file_name


def get_month_mean(rate_data):#获取利率数据的月均值
    rate_data = rate_data.rename(index=rate_data[rate_data.columns[0]])#把日期设置为索引
    rate_data = rate_data.dropna()
    rate_data[rate_data.columns[0]] = rate_data.index
    rate_data[rate_data.columns[0]] = rate_data[rate_data.columns[0]].apply(lambda x: str(x.year)+'-'+str(x.month))
    for i in range(1, rate_data.shape[1]):
        rate_data[rate_data.columns[i]] = pd.to_numeric(rate_data[rate_data.columns[i]], errors='coerce')
    rate_data = rate_data.groupby(rate_data.columns[0])[[rate_data.columns[i] for i in range(1, rate_data.shape[1])]].mean()
    rate_data['month'] = pd.to_datetime(rate_data.index)
    rate_data['month'] = rate_data['month'].apply(lambda x: str(x.year) + '-' + str(x.month)+'-'+str(x.days_in_month))
    rate_data.index = pd.to_datetime(rate_data[rate_data.columns[-1]])
    rate_data = rate_data[[rate_data.columns[i] for i in range(0, rate_data.shape[1]-1)]]#去除第一列的时间
    return rate_data.sort_index()

if __name__ == '__main__':
    start_time_1 = str(pd.to_datetime(start_time) - relativedelta(months=1))[0:7]
    end_time_1 = str(pd.to_datetime(end_time) + relativedelta(months=3))[0:7]
    filetype = ['.xls', 'xlsx']
    file_name = get_file_name(path, filetype)
    file_name = np.array(file_name)
    file_name.sort()  # 存放资产的名称
    macro_data = pd.read_excel(path_macro)  # 导入宏观数据
    asset_data = [pd.read_excel(path + fname) for fname in file_name]  # 导入资产数据，放到一个列表里，每一个元素是一个dataframe
    asset_month_payoff = pd.DataFrame()#asset_month_payoff用以存放了12个资产的月收益率
    for j in range(0, asset_num):  # 计算每一个资产，每一季度的收益率
        data = asset_data[j] # 当前处理的资产赋值给data
        data = data[
            (data[data.columns[0]] < end_time_1) &
            (data[data.columns[0]] >= start_time_1) &
            (data[data.columns[1]] != '--')]
        data = data.rename(index=data[data.columns[0]])
        net_value = data[data.columns[1]].apply(lambda x: str(x).replace(',', '')).copy(deep = True)
        data[data.columns[1]] = pd.to_numeric(net_value, errors = 'coerce')
        data_month = data.rename(index=data[data.columns[0]])
        data_month.index = pd.to_datetime(data_month.index)
        payoff = data_month.resample('M').apply(lambda x: x[-1])[data.columns[1]].pct_change()
        asset_month_payoff[file_name[j].split('.')[0]] = payoff
    asset_month_payoff = asset_month_payoff.iloc[1:]#asset_month_payoff存放了12个资产的月收益率
    rate_data = pd.read_excel(path_rate)  # 导入一揽子利率数据
    rate_data = rate_data.iloc[2:]
    rate_data = get_month_mean(rate_data)
    ap = pd.DataFrame()
    for i in range(asset_num):#针对12个资产分别计算不同货币状态下的月均收益率和上涨频率
        performer = asset_performance(asset_month_payoff[asset_month_payoff.columns[i]], asset_month_payoff.columns[i],rate_data)
        ap[performer.asset_name] = performer.asset_performance()
    ap.to_csv('资产表现_1_8.csv')#将结果导入到csv中



# a = Timing(asset_month_payoff[asset_month_payoff.columns[0]], asset_month_payoff.columns[0],rate_data)
# a.asset_performancew(a.asset_data, a.signal_payoff)
