from WindPy import *
import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt

w.start()


#########目标指数市盈率#########
def index_profit():
    '''
    计算可投资的指数
    - 详细算法：
        - 当指定指数的PE_TTM小于其机会值（固定）时，该指数可买进。
    :return:
        - index_pe: DataFrame
    '''
    today = (datetime.now() - timedelta(1)).strftime("%Y%m%d")
    error_code, index_pe = w.wss("000015.SH,000300.SH,HSI.HI,SPX.GI,NDX.GI",
                                 "sec_name,pe_ttm,dividendyield2",
                                 "tradeDate=%s" % today,
                                 usedf=True)
    index_pe.loc['000015.SH', '机会值'] = 6.87
    index_pe.loc['000300.SH', '机会值'] = 11.22
    index_pe.loc['HSI.HI', '机会值'] = 9.38
    index_pe.loc['SPX.GI', '机会值'] = 16.21
    index_pe.loc['NDX.GI', '机会值'] = 19.18
    codes = index_pe[index_pe.PE_TTM < index_pe.机会值].index.tolist()
    index_pe.rename(columns={'DIVIDENDYIELD2': '股息率'})  # 查看该指数分红比例
    print('可投资的指数是：', codes)
    return index_pe


##########筛选股票############
def stock_profit(market='A股'):
    '''
    计算值得投资的股票
    - 详细算法：
        - A股：
        - 过去五年，净利润现金含量>80%，且平均值>100%
        - 过去五年，销售毛利率>40%
        - 上市超过3年
        - 过去五年，净资产收益率(ROE)>20%
        - 过去五年，分红比例>25%
        - 过去五年，资产负债率<60%
        - 港股：
        - 过去五年，净资产收益率>15%
        - 过去五年，净利润现金含量>80%，且平均值>100%
        - 过去五年，销售毛利率>40%
        - 上市超过3年
        - 过去五年，资产负债率<60%
        - 过去五年，分红比例>25%，互联网高科技公司除外
        - 美股：
        - 过去三年，净资产收益率>15%
        - 过去五年，经营活动净现金流量除以净利润>80%
        - 过去五年，净利润现金含量平均值>100%
        - 过去五年，销售毛利率>40%
        - 上市超过3年
        - 市值大于500亿
        - 过去五年，资产负债率<60%
        - 过去五年，区间分红总额/净利润>25（互联网高科技公司除外）
    :return:
        - 值得投资的股票，list

    '''
    today = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
    market_dict = {
        'A股': 'a001010100000000',
        '港股': 'a002010100000000',
        '美股': '1000022276000000'
    }
    roe_dict = {'A股': 20, '港股': 15, '美股': 0}

    code_list = w.wset("sectorconstituent",
                       "date=%s;sectorid=%s" % (today, market_dict[market]))
    it_list = []
    if market == '港股':
        it_codes = w.wset("sectorconstituent",
                          "date=%s;sectorid=1000004901000000" % today)
        it_list = it_codes.Data[1]

    # code_list.Data[1]为证券代码
    # code_list.Data[2]为证券名称
    # 获取数据
    def get_payratio(year):
        div_payoutRatio2 = w.wsd(code_list.Data[1], "div_payoutRatio2", "ED0D",
                                 "%i-12-31" % year,
                                 "year=%i;Period=Y;Days=Alldays" % year)
        div_payoutRatio2 = pd.DataFrame(columns=div_payoutRatio2.Codes,
                                        data=np.mat(div_payoutRatio2.Data),
                                        index=div_payoutRatio2.Times)
        return div_payoutRatio2

    error, netprofitcashcover = w.wsd(code_list.Data[1],
                                      "fa_netprofitcashcover",
                                      "ED-4Y",
                                      "%i-12-31" % (datetime.now().year - 1),
                                      "Period=Y;Days=Alldays",
                                      usedf=True)  # 净利润现金含量
    error, grossprofitmargin = w.wsd(code_list.Data[1],
                                     "grossprofitmargin",
                                     "ED-4Y",
                                     "%i-12-31" % (datetime.now().year - 1),
                                     "Period=Y;Days=Alldays",
                                     usedf=True)  # 销售毛利率
    ipo_listdays = w.wsd(code_list.Data[1], "ipo_listdays", 'ED0D', today,
                         "Period=Y;Days=Alldays")
    ipo_listdays = pd.DataFrame(columns=ipo_listdays.Codes,
                                data=np.mat(ipo_listdays.Data),
                                index=ipo_listdays.Times)  # 上市天数
    error, roe = w.wsd(code_list.Data[1],
                       "roe",
                       "ED-4Y",
                       "%i-12-31" % (datetime.now().year - 1),
                       "Period=Y;Days=Alldays",
                       usedf=True)  # 净资产收益率(ROE)
    error, debttoassets = w.wsd(code_list.Data[1],
                                "debttoassets",
                                "ED-4Y",
                                "%i-12-31" % (datetime.now().year - 1),
                                "Period=Y;Days=Alldays",
                                usedf=True)  # 资产负债率
    payratio = pd.DataFrame()
    for i in range(1, 6):
        year = datetime.now().year - i
        payratio = pd.concat([payratio, get_payratio(year)])  # 分红比例   #TODO:检查清洗数据方法是否能排除掉原本为空的数据（ShowBlank=-1）
    # 清洗数据
    npcc_unselect = netprofitcashcover[netprofitcashcover < 80]
    npcc_select_id = npcc_unselect.loc[:, (npcc_unselect.isnull().all())].columns
    npcc_select = netprofitcashcover[npcc_select_id]
    npcc_avg = npcc_select.mean()
    npcc_precise = npcc_avg[npcc_avg >= 100]
    gpm_unselect = grossprofitmargin[grossprofitmargin < 40]
    gpm_select_id = gpm_unselect.loc[:, (gpm_unselect.isnull().all())].columns
    gpm_select = grossprofitmargin[gpm_select_id]
    ipo_select = ipo_listdays[ipo_listdays > 365 * 3].dropna(how='any', axis=1)
    roe_unselect = roe[roe < roe_dict[market]]
    roe_select_id = roe_unselect.loc[:, (roe_unselect.isnull().all())].columns
    roe_select = roe[roe_select_id]
    payratio_unselect = payratio[payratio < 25]
    payratio_select_id = payratio_unselect.loc[:, (payratio_unselect.isnull().all())].columns
    payratio_select = payratio[payratio_select_id].dropna(axis=1, thresh=4)
    dta_unselect = debttoassets[debttoassets > 60]
    dta_select_id = dta_unselect.loc[:, (dta_unselect.isnull().all())].columns
    dta_select = debttoassets[dta_select_id]
    # 筛选代码
    all_list = [
        npcc_precise.index.tolist(),
        gpm_select.columns.tolist(),
        ipo_select.columns.tolist(),
        roe_select.columns.tolist(),
        payratio_select.columns.tolist() + it_list,
        dta_select.columns.tolist()
    ]
    result = set.intersection(*map(set, all_list))
    print('筛选出的股票代码：', list(result))
    return list(result)


#########等待好价格##########
def good_price(stocks, market='A股'):
    '''
    计算给定股票是否值得购买
    - 详细算法：
        - A股：
        - 深证A股的市盈率<20
        - 给定股票的TTM市盈率<15
        - 给定股票的动态股息率>10年期国债收益率
        - 港股：
        - 恒生指数市盈率<10
        - 给定股票的TTM市盈率<15
        - 给定股票的动态股息率>10年期国债收益率
    :param stocks:给定股票，list
    :return:
        - codes：值得购买的股票，list
        - ten_rate：十年期国债收益率，float
        - sec_pe['PE_TTM']['399001.SZ']：深证A股的市盈率，float
    '''
    today = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
    market_dict = {'A股': '399001.SZ', '港股': 'HSI.HI'}
    pe_dict = {'A股': 20, '港股': 10}
    # 十年期国债收益率
    error, nat_debt = w.edb("M0325687",
                            "ED0D",
                            today,
                            "Fill=Previous",
                            usedf=True)
    ten_rate = nat_debt.iloc[0, 0]
    # 好价格指标
    error, sec_pe = w.wss(stocks + ["399001.SZ", 'HSI.HI'],
                          "pe_ttm,eps_ttm,close,dividendyield2",
                          "tradeDate=%s" % today,
                          usedf=True)
    sec_pe['好价格1'] = 15 * (sec_pe['CLOSE'] / sec_pe['PE_TTM'])
    sec_pe['好价格2'] = sec_pe.EPS_TTM / ten_rate * 100
    sec_pe['好价格'] = sec_pe[['好价格1', '好价格2']].min(axis=1)
    stock_df = sec_pe.iloc[:-2][
        (sec_pe.PE_TTM <= 15)
        & (sec_pe.DIVIDENDYIELD2 >= ten_rate)]
    codes = stock_df.index.tolist()
    prices = stock_df.好价格.tolist()
    if sec_pe['PE_TTM'][market_dict[market]] <= pe_dict[market]:
        print(
            '%s市盈率为%f，低于%i，处于安全区间。\n当前可购买的股票为：' %
            (market, sec_pe['PE_TTM'][market_dict[market]], pe_dict[market]),
            codes, '其好价格为：', prices)
    else:
        print(
            '%s市盈率为%f，高于%i，处于非安全区间，请谨慎投资。\n当前可购买的股票为：' %
            (market, sec_pe['PE_TTM'][market_dict[market]], pe_dict[market]),
            codes, '其好价格为：', prices)
    print('全量好价格：\n', sec_pe[['CLOSE', '好价格1', '好价格2', '好价格']].iloc[:-2])
    return codes, ten_rate, sec_pe['PE_TTM'][market_dict[market]]


#########卖出股票#########
def sell_stock(stocks, ten_rate, market_pe, market='A股'):
    '''
    计算给定股票是否需要卖出
    - 详细算法：
        - A股：
        - 深证A股的市盈率>60
        - 给定股票的TTM市盈率>50
        - 给定股票的动态股息率<10年期国债收益率的1/3
        - 港股：
        - 恒生指数的市盈率>20
        - 给定股票的TTM市盈率>40
        - 给定股票的动态股息率<10年期国债收益率的1/3
    :param stocks:给定股票，list
    :param ten_rate:十年期国债收益率，float
    :param stocks:深证A股的市盈率，float
    :return:
        - codes: 需要卖出的股票，list
    '''
    market_dict = {'A股': '399001.SZ', '港股': 'HSI.HI'}
    pe_dict = {'A股': 60, '港股': 20}
    st_pe_dict = {'A股': 50, '港股': 40}
    if (market_pe > pe_dict[market]) | (stocks == []):
        print('当前需卖出的股票为：', stocks)
        return stocks
    else:
        today = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
        error, sec_pe = w.wss(stocks,
                              "pe_ttm,dividendyield2",
                              "tradeDate=%s" % today,
                              usedf=True)
        codes = sec_pe[(sec_pe.PE_TTM > st_pe_dict[market]) | (
                sec_pe.DIVIDENDYIELD2 < ten_rate * 1 / 3)].index.tolist()
        print('当前需卖出的股票为：', codes)
        return codes


def calc_SMA(codes):
    error, sec_close = w.wsd(codes, "close", "1999-01-01", "2023-03-16", "TradingCalendar=SZSE", usedf=True)
    sec_close.dropna(how='all', inplace=True)
    sma_short = sec_close.rolling(window=42).mean()  # 短期
    sma_long = sec_close.rolling(window=252).mean()  # 长期
    positions = pd.DataFrame(np.where(sma_short > sma_long, 1, -1), columns=sma_short.columns, index=sma_short.index)
    # 将所有数据框的列按照名称进行匹配，存储在一个字典中
    col_dict = {}
    for col_name in sec_close.columns:
        col_dict[col_name] = [sec_close[col_name], sma_short[col_name], sma_long[col_name], positions[col_name]]

    # 创建子图
    n_cols = 1
    n_rows = len(col_dict)
    fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(10, 8))
    axes = axes.flatten()

    # 循环添加数据
    for i, (name, cols) in enumerate(col_dict.items()):
        for j, col in enumerate(cols):
            # 创建子图
            ax = axes[i]
            if j == len(cols) - 1:
                # 创建第二个y轴
                ax2 = ax.twinx()
                ax2.plot(col, label=name, color='tab:orange')
                ax2.set_ylabel('df3 ' + name, color='tab:orange')
                ax2.tick_params(axis='y', labelcolor='tab:orange')
            else:
                ax.plot(col, label=name)

        ax.set_title(name)
        ax.set_xlabel('Index')
        ax.set_ylabel(name)

    # 添加图例
    fig.legend(labels=['sec_close', 'sma_short', 'sma_long', 'positions'], loc='lower right')

    # 调整子图间距
    fig.tight_layout(pad=3.0)

    # 显示图形
    plt.show()


if __name__ == '__main__':
    market = 'A股'
    index_buy = index_profit()
    stock_select = stock_profit(market)
    stock_buy, ten_rate, market_pe = good_price(stock_select, market)
    stock_sell = sell_stock(['002677.SZ'], ten_rate, market_pe, market)
    calc_SMA(stock_buy)

    market = '港股'
    stock_select = stock_profit(market)
    stock_buy, ten_rate, market_pe = good_price(stock_select, market)
    stock_sell = sell_stock(stock_buy, ten_rate, market_pe, market)
