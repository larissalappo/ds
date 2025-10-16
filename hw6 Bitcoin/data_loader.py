import yfinance as yf
import pandas as pd
def download_bitcoin_data(period='3y'):
    """
    Загрузка данных о курсе Bitcoin с Yahoo Finance.

    Args:
        period: период данных (1y, 2y, 3y и т.д.)

    Returns:
        pd.DataFrame: DataFrame с данными о цене Bitcoin
    """
    try:
        ticker = yf.Ticker('BTC-USD')
        hist = ticker.history(period=period)

        df = pd.DataFrame({
            'date': hist.index,
            'price': hist['Close']
        }).reset_index(drop=True)

        print(f"Загружено {len(df)} записей Bitcoin")
        print(f"Период данных: {df['date'].min()} - {df['date'].max()}")
        print("Загрузка завершена успешно")
        print("="*70)
        return df

    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return None
def main_data_loader():
    """Основная функция загрузки данных для анализа временного ряда Bitcoin"""

    # Загрузка данных Bitcoin
    df = download_bitcoin_data(period='3y')
    if df is None:
        return

if __name__ == "__main__":
   main_data_loader()
