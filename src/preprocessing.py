from sklearn.preprocessing import StandardScaler
from pandas_ta import log_return
import pandas as pd
import numpy as np
import talib
import warnings


def renaming(df: pd.DataFrame):
    """rename columns"""
    df.rename(
        columns={
            "close_price": "close",
            "high_price": "high",
            "low_price": "low",
            "open_price": "open",
        },
        inplace=True,
    )
    return df


def keep_essentials(df: pd.DataFrame):
    """Keep only OHLCVT"""
    df.drop(
        columns=["exchange", "turnover", "symbol"],
        axis=1,
        inplace=True,
    )
    return renaming(df)


def prepare_desired_pos(df, lag, multiplier):
    print('Generating desired position...')
    df = df.copy()
    scaler = StandardScaler()
    df[f"{lag}m_ret"] = scaler.fit_transform(
        log_return(df.close, length=lag, offset=-lag).values.reshape(-1, 1)
    )
    df.dropna(inplace=True)
    df["desired_pos_change"] = (df[f"{lag}m_ret"] * multiplier).apply(int)
    df["desired_pos_rolling"] = (
        df["desired_pos_change"].rolling(lag, min_periods=1).sum().apply(int)
    )
    df['desired_pos_change'] = df['desired_pos_change'] - df[
        'desired_pos_change'].shift(lag).fillna(0)
    df["pos_change_signal"] = pd.qcut(
        df["desired_pos_change"], 5,
        ["strong sell", "sell", "meh", "buy", "strong buy"]
    )
    df["net_pos_signal"] = np.where(
        df["desired_pos_rolling"] > 0, "long hold", "short hold"
    )
    df.drop(columns=[f"{lag}m_ret"], inplace=True)
    print("Desired position generated")

    return df


def rle(df, plot=False):
    """Run length encoding"""
    mask = df["pos_change_signal"].ne(df["pos_change_signal"].shift())
    groups = mask.cumsum()
    rle_result = df.groupby(groups)["pos_change_signal"].agg([
        ("value", "first"), ("count", "size")
    ])
    if plot:
        rle_result.groupby("value").mean().plot(
            kind="bar", title="Average count of consecutive same values"
        )
    return rle_result


def generate_og_features_df(df: pd.DataFrame, lags: list):
    print("Generating original features...")
    for lag in lags:
        df["ADOSC_" + str(lag)] = talib.ADOSC(
            df["high"], df["low"], df["close"], df["volume"], lag, lag * 3
        )
        df["MFI_" + str(lag)] = talib.MFI(
            df["high"], df["low"], df["close"], df["volume"], lag
        )


def generate_mom_features_df(df: pd.DataFrame, lags: list):
    print("Generating momentum features...")
    for lag in lags:
        df["ROC_" + str(lag)] = talib.ROC(df["close"], lag)
        df["MOM_" + str(lag)] = talib.MOM(df["close"], lag)
        df["PLUS_DM_" + str(lag)] = talib.PLUS_DM(df["high"], df["low"], lag)
        df["MINUS_DM_" + str(lag)] = talib.MINUS_DM(df["high"], df["low"], lag)
        df["ADX_" +
           str(lag)] = talib.ADX(df["high"], df["low"], df["close"], lag)
        df["ADXR_" +
           str(lag)] = talib.ADXR(df["high"], df["low"], df["close"], lag)
        df["APO_" + str(lag)] = talib.APO(df["close"], lag, lag * 2)
        df["AROONOSC_" + str(lag)] = talib.AROONOSC(df["high"], df["low"], lag)

        df["CCI_" +
           str(lag)] = talib.CCI(df["high"], df["low"], df["close"], lag)
        df["CMO_" + str(lag)] = talib.CMO(df["close"], lag)
        df["DX_" +
           str(lag)] = talib.DX(df["high"], df["low"], df["close"], lag)
        df["STOCH_" + str(lag) + "slowk"], _ = talib.STOCH(
            df["high"],
            df["low"],
            df["close"],
            fastk_period=lag,
            slowk_period=int(lag / 2),
            slowk_matype=0,
            slowd_period=int(lag / 2),
            slowd_matype=0,
        )
        df["STOCHF_" + str(lag) + "fastk"], _ = talib.STOCHF(
            df["high"], df["low"], df["close"], lag, int(lag / 2), 0
        )
        (_, df["MACDSIGNAL_" + str(lag)],
         _) = talib.MACD(df["close"], lag, lag * 2, int(lag / 2))
        _, df["MACDSIGNALFIX_" + str(lag)], _ = talib.MACDFIX(df["close"], lag)
        df["PPO_" + str(lag)] = talib.PPO(df["close"], lag, lag * 2)
        df["RSI_" + str(lag)] = talib.RSI(df["close"], lag)
        df["ULTOSC_" + str(lag)] = talib.ULTOSC(
            df["high"], df["low"], df["close"], lag, lag * 2, lag * 3
        )
        df["WILLR_" +
           str(lag)] = talib.WILLR(df["high"], df["low"], df["close"], lag)
        df["STOCHRSI_" + str(lag) +
           "k"], _ = talib.STOCHRSI(df["close"], lag, 3, 3)
        df["NATR_" +
           str(lag)] = talib.NATR(df["high"], df["low"], df["close"], lag)
        df["ATR_" +
           str(lag)] = talib.ATR(df["high"], df["low"], df["close"], lag)
        df["TRANGE_" +
           str(lag)] = talib.TRANGE(df["high"], df["low"], df["close"])

    df["HT_TRENDLINE"] = talib.HT_TRENDLINE(df["close"])
    df["HT_TRENDMODE"] = talib.HT_TRENDMODE(df["close"])
    df["HT_DCPERIOD"] = talib.HT_DCPERIOD(df["close"])
    df["HT_DCPHASE"] = talib.HT_DCPHASE(df["close"])
    df["HT_PHASORinphase"], _ = talib.HT_PHASOR(df["close"])
    df["HT_SINEsine"], _ = talib.HT_SINE(df["close"])


def generate_math_features_df(df: pd.DataFrame, lags: list):
    print("Generating math features...")
    for lag in lags:
        df["BETA_" + str(lag)] = talib.BETA(df["high"], df["low"], lag)
        df["CORREL_" + str(lag)] = talib.CORREL(df["high"], df["low"], lag)
        df["LINEARREG_" + str(lag)] = talib.LINEARREG(df["close"], lag)
        df["LINEARREG_ANGLE_" +
           str(lag)] = talib.LINEARREG_ANGLE(df["close"], lag)
        df["LINEARREG_INTERCEPT_" +
           str(lag)] = talib.LINEARREG_INTERCEPT(df["close"], lag)
        df["LINEARREG_SLOPE_" +
           str(lag)] = talib.LINEARREG_SLOPE(df["close"], lag)
        df["STDDEV_" + str(lag)] = talib.STDDEV(df["close"], lag)
        df["TSF_" + str(lag)] = talib.TSF(df["close"], lag)
        df["VAR_" + str(lag)] = talib.VAR(df["close"], lag)


def generate_pattern_features_df(df: pd.DataFrame):
    print("Generating pattern features...")
    df["CDL2CROWS"] = talib.WMA(
        talib.CDL2CROWS(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDL3BLACKCROWS"] = talib.WMA(
        talib.CDL3BLACKCROWS(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDL3INSIDE"] = talib.WMA(
        talib.CDL3INSIDE(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDL3LINESTRIKE"] = talib.WMA(
        talib.CDL3LINESTRIKE(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDL3OUTSIDE"] = talib.WMA(
        talib.CDL3OUTSIDE(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDL3STARSINSOUTH"] = talib.WMA(
        talib.CDL3STARSINSOUTH(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDL3WHITESOLDIERS"] = talib.WMA(
        talib.CDL3WHITESOLDIERS(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLABANDONEDBABY"] = talib.WMA(
        talib.CDLABANDONEDBABY(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLADVANCEBLOCK"] = talib.WMA(
        talib.CDLADVANCEBLOCK(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLBELTHOLD"] = talib.WMA(
        talib.CDLBELTHOLD(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLBREAKAWAY"] = talib.WMA(
        talib.CDLBREAKAWAY(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLCLOSINGMARUBOZU"] = talib.WMA(
        talib.CDLCLOSINGMARUBOZU(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )

    df["CDLCONCEALBABYSWALL"] = talib.WMA(
        talib.CDLCONCEALBABYSWALL(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLCOUNTERATTACK"] = talib.WMA(
        talib.CDLCOUNTERATTACK(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLDARKCLOUDCOVER"] = talib.WMA(
        talib.CDLDARKCLOUDCOVER(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLDOJI"] = talib.WMA(
        talib.CDLDOJI(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLDOJISTAR"] = talib.WMA(
        talib.CDLDOJISTAR(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLDRAGONFLYDOJI"] = talib.WMA(
        talib.CDLDRAGONFLYDOJI(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLENGULFING"] = talib.WMA(
        talib.CDLENGULFING(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLEVENINGDOJISTAR"] = talib.WMA(
        talib.CDLEVENINGDOJISTAR(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLEVENINGSTAR"] = talib.WMA(
        talib.CDLEVENINGSTAR(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLGAPSIDESIDEWHITE"] = talib.WMA(
        talib.CDLGAPSIDESIDEWHITE(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLGRAVESTONEDOJI"] = talib.WMA(
        talib.CDLGRAVESTONEDOJI(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLHAMMER"] = talib.WMA(
        talib.CDLHAMMER(df["open"], df["high"], df["low"], df["close"]), 300
    )

    df["CDLHANGINGMAN"] = talib.WMA(
        talib.CDLHANGINGMAN(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLHARAMI"] = talib.WMA(
        talib.CDLHARAMI(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLHARAMICROSS"] = talib.WMA(
        talib.CDLHARAMICROSS(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLHIGHWAVE"] = talib.WMA(
        talib.CDLHIGHWAVE(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLHIKKAKE"] = talib.WMA(
        talib.CDLHIKKAKE(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLHIKKAKEMOD"] = talib.WMA(
        talib.CDLHIKKAKEMOD(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLHOMINGPIGEON"] = talib.WMA(
        talib.CDLHOMINGPIGEON(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLIDENTICAL3CROWS"] = talib.WMA(
        talib.CDLIDENTICAL3CROWS(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLINNECK"] = talib.WMA(
        talib.CDLINNECK(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLINVERTEDHAMMER"] = talib.WMA(
        talib.CDLINVERTEDHAMMER(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLKICKING"] = talib.WMA(
        talib.CDLKICKING(df["open"], df["high"], df["low"], df["close"]), 300
    )

    df["CDLKICKINGBYLENGTH"] = talib.WMA(
        talib.CDLKICKINGBYLENGTH(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLLADDERBOTTOM"] = talib.WMA(
        talib.CDLLADDERBOTTOM(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLLONGLEGGEDDOJI"] = talib.WMA(
        talib.CDLLONGLEGGEDDOJI(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLLONGLINE"] = talib.WMA(
        talib.CDLLONGLINE(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLMARUBOZU"] = talib.WMA(
        talib.CDLMARUBOZU(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLMATCHINGLOW"] = talib.WMA(
        talib.CDLMATCHINGLOW(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLMATHOLD"] = talib.WMA(
        talib.CDLMATHOLD(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLMORNINGDOJISTAR"] = talib.WMA(
        talib.CDLMORNINGDOJISTAR(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLMORNINGSTAR"] = talib.WMA(
        talib.CDLMORNINGSTAR(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLONNECK"] = talib.WMA(
        talib.CDLONNECK(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLPIERCING"] = talib.WMA(
        talib.CDLPIERCING(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLRICKSHAWMAN"] = talib.WMA(
        talib.CDLRICKSHAWMAN(df["open"], df["high"], df["low"], df["close"]),
        300
    )

    df["CDLRISEFALL3METHODS"] = talib.WMA(
        talib.CDLRISEFALL3METHODS(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLSEPARATINGLINES"] = talib.WMA(
        talib.CDLSEPARATINGLINES(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLSHOOTINGSTAR"] = talib.WMA(
        talib.CDLSHOOTINGSTAR(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLSHORTLINE"] = talib.WMA(
        talib.CDLSHORTLINE(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLSPINNINGTOP"] = talib.WMA(
        talib.CDLSPINNINGTOP(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLSTALLEDPATTERN"] = talib.WMA(
        talib.CDLSTALLEDPATTERN(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLSTICKSANDWICH"] = talib.WMA(
        talib.CDLSTICKSANDWICH(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLTAKURI"] = talib.WMA(
        talib.CDLTAKURI(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLTASUKIGAP"] = talib.WMA(
        talib.CDLTASUKIGAP(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLTHRUSTING"] = talib.WMA(
        talib.CDLTHRUSTING(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLTRISTAR"] = talib.WMA(
        talib.CDLTRISTAR(df["open"], df["high"], df["low"], df["close"]), 300
    )
    df["CDLUNIQUE3RIVER"] = talib.WMA(
        talib.CDLUNIQUE3RIVER(df["open"], df["high"], df["low"], df["close"]),
        300
    )
    df["CDLUPSIDEGAP2CROWS"] = talib.WMA(
        talib.CDLUPSIDEGAP2CROWS(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )
    df["CDLXSIDEGAP3METHODS"] = talib.WMA(
        talib.CDLXSIDEGAP3METHODS(
            df["open"], df["high"], df["low"], df["close"]
        ), 300
    )


def generate_time_features(df: pd.DataFrame):
    print("Generating time features...")
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["time_hour"] = df["datetime"].dt.hour
    df["time_minute"] = df["datetime"].dt.minute
    df["time_day_of_week"] = df["datetime"].dt.dayofweek
    df["time_day_of_month"] = df["datetime"].dt.day
    df.drop(columns=["datetime"], inplace=True)


def generate_all_features_df(df: pd.DataFrame, lags: list):

    warnings.filterwarnings("ignore")
    generate_og_features_df(df, lags)
    generate_mom_features_df(df, lags)
    generate_math_features_df(df, lags)
    generate_pattern_features_df(df)
    generate_time_features(df)
    df.dropna(inplace=True)

    # sort by name
    df = df.reindex(sorted(df.columns), axis=1)
    print("All features generated")
    return df


def drop_ohlcv_cols(df: pd.DataFrame):
    """drop ohlcv columns"""
    return df.drop(
        columns=["open", "high", "low", "close", "volume", "open_interest"],
        axis=1
    )


def split_features_target(df: pd.DataFrame):
    """split features and target"""
    print("Splitting features/target")
    X = df.drop([
        'pos_change_signal', 'net_pos_signal', 'desired_pos_change',
        'desired_pos_rolling'
    ],
                axis=1)
    y = df[[
        'pos_change_signal', 'net_pos_signal', 'desired_pos_change',
        'desired_pos_rolling'
    ]]
    print('Features/target split complete')

    return X, y


def prep_data(df: pd.DataFrame, lags: list, lag: int, multiplier: int):
    """prep data for training"""
    df = keep_essentials(df)
    df = prepare_desired_pos(df, lag, multiplier)
    df = generate_all_features_df(df, lags)
    df = drop_ohlcv_cols(df)
    X, y = split_features_target(df)
    return X, y