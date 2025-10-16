
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, acf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
from math import sqrt
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
from data_loader import download_bitcoin_data

def prepare_stationary_data(df):
    """
    Подготовка стационарных данных.

    Args:
        df: DataFrame с исходными данными

    Returns:
        tuple: stationary_series, df_prepared
    """

    # Детальный анализ данных
    print('='*70)
    print("Детальный анализ исходных данных:")
    print(f"Пропуски в данных: {df['price'].isna().sum()}")

    # Статистики
    print("\nСтатистики исходного ряда:")
    print(df['price'].describe())

    # Проверим на выбросы
    Q1 = df['price'].quantile(0.25)
    Q3 = df['price'].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df['price'] < (Q1 - 1.5 * IQR)) | (df['price'] > (Q3 + 1.5 * IQR))]
    print(f"\nВыбросы: {len(outliers)} точек")

    # # Визуализируем выбросы
    # plt.figure(figsize=(12, 6))
    # plt.plot(df['date_rate'], df['rate'], label='BTC-USD', alpha=0.7)
    # if len(outliers) > 0:
    #     plt.scatter(outliers['date_rate'], outliers['rate'], color='red', s=50, label='Выбросы')
    # plt.title('Bitcoin Price с выделением выбросов')
    # plt.legend()
    # plt.show()

    # Тест Дики-Фуллера
    print('='*70)
    print('Тест ADF на исходных данных:')
    result = adfuller(df['price'])
    print('ADF Statistic: %f' % result[0])
    print('p-value: %f' % result[1])
    print('Critical Values:')
    for key, value in result[4].items():
        print('\t%s: %.3f' % (key, value))

    # Интерпретация:
    if result[1] <= 0.05:
        print('Ряд СТАЦИОНАРЕН (отвергаем H₀)')
    else:
        print('Ряд НЕСТАЦИОНАРЕН (не отвергаем H₀)')

    # Дифференцирование 1 порядка
    print('='*70)
    print('Дифференцирование первого порядка')
    df_diff = df.copy()  # Создаем копию DataFrame
    df_diff['price_diff'] = df['price'].diff()  # Дифференцируем только цену
    df_diff = df_diff.dropna()  # Удаляем NaN

    # Тест ADF (после дифференцирования)
    print('='*70)
    print('Тест ADF после дифференцирования')
    result_diff = adfuller(df_diff['price'])
    print('ADF Statistic (после дифференцирования):', result_diff[0])
    print('p-value (после дифференцирования):', result_diff[1])

    # Интерпретация для дифференцированных данных:
    if result_diff[1] <= 0.05:
        print('Ряд СТАЦИОНАРЕН после дифференцирования')
    else:
        print('Ряд НЕСТАЦИОНАРЕН после дифференцирования')

    # Дифференцирование 2 порядка
    print('='*70)
    print('Дифференцирование 2 порядка')
    df_diff_2 = df_diff.copy()  # Создаем копию DataFrame
    df_diff_2['price_diff_2'] = df_diff['price_diff'].diff()  # Дифференцируем только цену
    df_diff_2 = df_diff_2.dropna()  # Удаляем NaN

    # Тест ADF (после двойного дифференцирования)
    print('='*70)
    print('Тест ADF после двойного дифференцирования')
    result_diff_2 = adfuller(df_diff_2['price_diff'])
    print('ADF Statistic (после 2 дифференцирования):', result_diff_2[0])
    print('p-value (после 2 дифференцирования):', result_diff_2[1])

    # Интерпретация для дифференцированных данных:
    if result_diff_2[1] <= 0.05:
        print('Ряд СТАЦИОНАРЕН после двойного дифференцирования')
    else:
        print('Ряд НЕСТАЦИОНАРЕН после двойного дифференцирования')

    # Статистика после двойного дифференцирования
    print()
    print('Статистика после двойного дифференцирования:')
    print(f"Среднее изменение: {df_diff_2['price_diff_2'].mean():.2f}")
    print(f"Стандартное отклонение: {df_diff_2['price_diff_2'].std():.2f}")
    print(f"Минимальное изменение: {df_diff_2['price_diff_2'].min():.2f}")
    print(f"Максимальное изменение: {df_diff_2['price_diff_2'].max():.2f}")

    # Процентные изменения
    print('='*70)
    print('Процентные изменения:')
    df_pct = df.copy()
    df_pct['pct_change'] = df['price'].pct_change() * 100  # В процентах
    df_pct = df_pct.dropna()

    stationary_series_pct = df_pct['pct_change']

    # Тест ADF на процентных изменениях
    result_pct = adfuller(stationary_series_pct)
    print(f'ADF Statistic: {result_pct[0]:.6f}')
    print(f'p-value: {result_pct[1]:.6f}')

    if result_pct[1] <= 0.05:
        print('Ряд СТАЦИОНАРЕН после преобразования в процентные изменения')
    else:
        print('Ряд НЕСТАЦИОНАРЕН')

    # Статистики процентных изменений
    print(f"\nСтатистики процентных изменений:")
    print(f"Среднее дневное изменение: {stationary_series_pct.mean():.4f}%")
    print(f"Стандартное отклонение: {stationary_series_pct.std():.4f}%")
    print(f"Минимальное изменение: {stationary_series_pct.min():.4f}%")
    print(f"Максимальное изменение: {stationary_series_pct.max():.4f}%")

    # Логарифмические returns (более стабильная дисперсия)
    print('='*70)
    print('Логарифмические изменения:')
    df_prepared = df.copy()
    df_prepared['log_return'] = np.log(df_prepared['price'] / df_prepared['price'].shift(1))
    df_prepared = df_prepared.dropna()

    stationary_series = df_prepared['log_return'].reset_index(drop=True)

    # Тест ADF на логарифмических изменениях
    adf_result = adfuller(stationary_series)
    print(f'ADF Statistic: {adf_result[0]:.6f}')
    print(f"ADF test p-value: {adf_result[1]:.6f}")
    if adf_result[1] <= 0.05:
        print("Ряд стационарен после преобразования в логарифмические изменения")
    else:
        print("Ряд нестационарен")

    # Статистики логарифмических изменений
    print(f"\nСтатистики логарифмических изменений:")
    print(f"Среднее дневное изменение: {stationary_series.mean():.4f}%")
    print(f"Стандартное отклонение: {stationary_series.std():.4f}%")
    print(f"Минимальное изменение: {stationary_series.min():.4f}%")
    print(f"Максимальное изменение: {stationary_series.max():.4f}%")

    # Визуализируем все 4 варианта
    fig, axes = plt.subplots(4, 1, figsize=(12, 10))

    # # Исходные данные
    # axes[0].plot(df['date'], df['price'])
    # axes[0].set_title('Bitcoin Price - Исходные данные')
    # axes[0].set_ylabel('Price (USD)')
    # axes[0].grid(True)

    # Абсолютные изменения (первое дифференцирование)
    axes[0].plot(df_diff['date'], df_diff['price_diff'])
    axes[0].set_title('Абсолютные изменения (первое дифференцирование)')
    axes[0].set_ylabel('Change (USD)')
    axes[0].grid(True)

    # Абсолютные изменения (второе дифференцирование)
    axes[1].plot(df_diff_2['date'], df_diff_2['price_diff_2'])
    axes[1].set_title('Абсолютные изменения (второе дифференцирование)')
    axes[1].set_ylabel('Change (USD)')
    axes[1].grid(True)

    # Процентные изменения
    axes[2].plot(df_pct['date'], stationary_series_pct)
    axes[2].set_title('Процентные изменения')
    axes[2].set_ylabel('Change (%)')
    axes[2].set_xlabel('Date')
    axes[2].grid(True)

    # Логарифмические изменения
    axes[3].plot(df_prepared['date'], stationary_series)
    axes[3].set_title('Логарифмические изменения (returns)')
    axes[3].set_ylabel('Change (%)')
    axes[3].set_xlabel('Date')
    axes[3].grid(True)

    plt.tight_layout()
    plt.show()

    # Синхронизация дат и данных
    # После dropna() у нас меньше строк в df_prepared, чем в исходном df
    print("Синхронизация дат и данных (После dropna() у нас меньше строк в df_prepared, чем в исходном df)")
    df_prepared = df_prepared['date'].iloc[1:]  # Пропускаем первую дату (там NaN из-за shift)
    stationary_series = stationary_series.iloc[1:]  # Пропускаем первый элемент

    print("="*70)
    print("Статистика по синхронизированным данным:")
    print(f"Размер df_prepared: {len(df_prepared)}")
    print(f"Размер stationary_series: {len(stationary_series)}")
    print("Подготовка данных завершена успешно")
    print("="*70)

    return stationary_series, df_prepared

def main_data_processing():
    """Основная функция загрузки и подготовки данных для анализа временного ряда Bitcoin"""
    # Отключение предупреждений
    warnings.filterwarnings("ignore")

    # Загрузка данных Bitcoin
    df = download_bitcoin_data(period='3y')
    if df is None:
        return

    # Исследование данных
    print("Исследование данных:")
    print("Первые 5 строк:")
    print(df.head())
    print(f"\nРазмер данных: {df.shape}")
    print(f"\nТипы данных:")

    # Визуализация исходных данных
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['price'], linewidth=1)
    plt.title('Историческая цена Bitcoin')
    plt.xlabel('Дата')
    plt.ylabel('Цена (USD)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    # Подготовка стационарных данных
    stationary_data, df_prepared = prepare_stationary_data(df)


if __name__ == "__main__":
    main_data_processing()
