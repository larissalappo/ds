
"""
Модуль для построения модели ARIMA для прогнозирования курса Биткоина.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
from math import sqrt
from datetime import timedelta


class ARIMAModel:
    """
    Класс для построения и оценки модели ARIMA.
    """

    def __init__(self):
        """Инициализация модели ARIMA."""
        self.model = None
        self.model_fit = None
        self.forecast = None
        self.forecast_index = None

    def analyze_acf_pacf(self, stationary_series, lags=40):
        """
        Анализ ACF и PACF для определения параметров ARIMA.

        Args:
            stationary_series: стационарный временной ряд
            lags: количество лагов для анализа
        """
        print("=" * 70)
        print("АНАЛИЗ ACF И PACF")
        print("=" * 70)

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # ACF plot
        plot_acf(stationary_series, ax=axes[0], lags=lags, alpha=0.05)
        axes[0].set_title('Autocorrelation Function (ACF)')
        axes[0].set_ylabel('ACF')
        axes[0].grid(True, alpha=0.3)

        # PACF plot
        plot_pacf(stationary_series, ax=axes[1], lags=lags, alpha=0.05, method='ywm')
        axes[1].set_title('Partial Autocorrelation Function (PACF)')
        axes[1].set_ylabel('PACF')
        axes[1].set_xlabel('Lag')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        # Вычисление значимых лагов
        acf_values = acf(stationary_series, nlags=lags, fft=False)

        # Определение значимых лагов (выше 95% доверительного интервала)
        significant_acf_lags = np.where(np.abs(acf_values) > 1.96 / np.sqrt(len(stationary_series)))[0]

        print(f"Значимые лаги ACF: {significant_acf_lags[:5]}")
        print(f"Всего значимых лагов ACF: {len(significant_acf_lags)}")

        return significant_acf_lags

    def split_data(self, stationary_series, test_size=0.2):
        """
        Разделение данных на обучающую и тестовую выборки.

        Args:
            stationary_series: стационарный временной ряд
            test_size: доля тестовой выборки

        Returns:
            tuple: train_data, test_data
        """
        split_point = int(len(stationary_series) * (1 - test_size))
        train_data = stationary_series[:split_point]
        test_data = stationary_series[split_point:]

        print(f"Размер обучающей выборки: {len(train_data)}")
        print(f"Размер тестовой выборки: {len(test_data)}")
        print(f"Период обучения: {len(train_data) / len(stationary_series) * 100:.1f}% данных")

        return train_data, test_data

    def fit_arima_model(self, train_data, order=(1, 0, 1)):
        """
        Обучение модели ARIMA.

        Args:
            train_data: обучающие данные
            order: параметры (p, d, q) модели ARIMA

        Returns:
            fitted_model: обученная модель
        """
        print(f"Обучение модели ARIMA{order}")

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                self.model = ARIMA(train_data, order=order)
                self.model_fit = self.model.fit()

            print("Модель успешно обучена")
            print(f"AIC: {self.model_fit.aic:.3f}")
            print(f"BIC: {self.model_fit.bic:.3f}")
            print(f"HQIC: {self.model_fit.hqic:.3f}")

            return self.model_fit

        except Exception as error:
            print(f"Ошибка при обучении модели: {error}")
            raise

    def evaluate_model(self, test_data, forecast_steps=None):
        """
        Оценка модели на тестовых данных.

        Args:
            test_data: тестовые данные
            forecast_steps: количество шагов прогноза

        Returns:
            tuple: predictions, metrics
        """
        if self.model_fit is None:
            raise ValueError("Модель не обучена. Сначала вызовите fit_arima_model.")

        if forecast_steps is None:
            forecast_steps = len(test_data)

        print(f"Прогнозирование на {forecast_steps} шагов")

        try:
            # Прогноз на тестовой выборке
            forecast_result = self.model_fit.get_forecast(steps=forecast_steps)
            predictions = forecast_result.predicted_mean
            confidence_intervals = forecast_result.conf_int()

            # Вычисление метрик
            actual_values = test_data.values[:forecast_steps]
            mse = mean_squared_error(actual_values, predictions)
            rmse = sqrt(mse)
            mae = mean_absolute_error(actual_values, predictions)
            mape = np.mean(np.abs((actual_values - predictions) / actual_values)) * 100

            metrics = {
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'mape': mape
            }

            print("Метрики качества модели:")
            print(f"MSE: {mse:.6f}")
            print(f"RMSE: {rmse:.6f}")
            print(f"MAE: {mae:.6f}")
            print(f"MAPE: {mape:.2f}%")

            return predictions, confidence_intervals, metrics

        except Exception as error:
            print(f"Ошибка при прогнозировании: {error}")
            raise

    def grid_search_arima(self, train_data, p_range, d_range, q_range):
        """
        Поиск лучших параметров ARIMA с помощью grid search.

        Args:
            train_data: обучающие данные
            p_range: диапазон значений для p
            d_range: диапазон значений для d
            q_range: диапазон значений для q

        Returns:
            DataFrame: результаты grid search
        """
        print("Запуск grid search для ARIMA")
        print(f"Диапазоны параметров: p={p_range}, d={d_range}, q={q_range}")

        best_aic = float('inf')
        best_order = None
        results = []

        for p in p_range:
            for d in d_range:
                for q in q_range:
                    order = (p, d, q)
                    try:
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore")
                            model = ARIMA(train_data, order=order)
                            model_fit = model.fit()

                        aic = model_fit.aic
                        results.append({
                            'order': order,
                            'aic': aic,
                            'bic': model_fit.bic
                        })

                        if aic < best_aic:
                            best_aic = aic
                            best_order = order
                            print(f"Новый лучший порядок: {best_order} с AIC={best_aic:.3f}")

                    except Exception:
                        continue

        results_df = pd.DataFrame(results).sort_values('aic')

        print(f"Лучшие параметры: {best_order} с AIC={best_aic:.3f}")
        print("Топ-5 моделей:")
        for i, row in results_df.head().iterrows():
            print(f"ARIMA{row['order']}: AIC={row['aic']:.3f}, BIC={row['bic']:.3f}")

        return results_df, best_order

    def plot_results(self, train_data, test_data, predictions, confidence_intervals):
        """
        Визуализация результатов прогнозирования.

        Args:
            train_data: обучающие данные
            test_data: тестовые данные
            predictions: прогнозы
            confidence_intervals: доверительные интервалы
        """
        plt.figure(figsize=(12, 8))

        # # Обучающие данные
        # plt.subplot(2, 1, 1)
        # plt.plot(train_data.index, train_data.values, label='Обучающие данные', color='blue')
        # plt.title('Обучающие данные - Логарифмические изменения цены Bitcoin')
        # plt.ylabel('Лог. изменения')
        # plt.legend()
        # plt.grid(True, alpha=0.3)

        # Тестовые данные и прогноз
        plt.subplot(2, 1, 2)
        test_index = range(len(train_data), len(train_data) + len(predictions))

        plt.plot(test_index, test_data.values[:len(predictions)],
                label='Фактические значения', color='green', alpha=0.7)
        plt.plot(test_index, predictions, label='Прогноз', color='red')

        # Доверительные интервалы
        plt.fill_between(
            test_index,
            confidence_intervals.iloc[:, 0],
            confidence_intervals.iloc[:, 1],
            color='red', alpha=0.1, label='95% Доверительный интервал'
        )

        plt.title('Прогноз vs Фактические значения')
        plt.xlabel('Временной индекс')
        plt.ylabel('Лог. изменения')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def forecast_future(self, steps=30, last_date=None):
        """
        Прогнозирование на будущие периоды.

        Args:
            steps: количество шагов прогноза
            last_date: последняя дата в данных

        Returns:
            tuple: forecast_values, confidence_intervals
        """
        if self.model_fit is None:
            raise ValueError("Модель не обучена. Сначала вызовите fit_arima_model.")

        print(f"Прогнозирование на {steps} будущих шагов")

        try:
            forecast_result = self.model_fit.get_forecast(steps=steps)
            forecast_values = forecast_result.predicted_mean
            confidence_intervals = forecast_result.conf_int()

            # Создание индекса для будущих дат
            if last_date is not None:
                self.forecast_index = pd.date_range(
                    start=last_date + timedelta(days=1),
                    periods=steps,
                    freq='D'
                )
            else:
                self.forecast_index = range(len(forecast_values))

            self.forecast = forecast_values

            print("Прогноз завершен")
            print(f"Среднее прогнозируемое изменение: {forecast_values.mean():.6f}")
            print(f"Диапазон прогноза: [{forecast_values.min():.6f}, {forecast_values.max():.6f}]")

            return forecast_values, confidence_intervals

        except Exception as error:
            print(f"Ошибка при прогнозировании будущего: {error}")
            raise

    def get_model_summary(self):
        """Получение summary модели."""
        if self.model_fit is None:
            raise ValueError("Модель не обучена.")

        return self.model_fit.summary()

    def get_residuals_analysis(self):
        """
        Анализ остатков модели.

        Returns:
            tuple: residuals, residuals_stats
        """
        if self.model_fit is None:
            raise ValueError("Модель не обучена.")

        residuals = self.model_fit.resid
        residuals_stats = {
            'mean': residuals.mean(),
            'std': residuals.std(),
            'skewness': residuals.skew(),
            'kurtosis': residuals.kurtosis()
        }

        print("Анализ остатков:")
        print(f"Среднее: {residuals_stats['mean']:.6f}")
        print(f"Стандартное отклонение: {residuals_stats['std']:.6f}")
        print(f"Асимметрия: {residuals_stats['skewness']:.6f}")
        print(f"Эксцесс: {residuals_stats['kurtosis']:.6f}")

        # Визуализация остатков
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        # Остатки временной ряд
        axes[0, 0].plot(residuals)
        axes[0, 0].set_title('Остатки модели')
        axes[0, 0].set_ylabel('Остатки')
        axes[0, 0].grid(True, alpha=0.3)

        # Гистограмма остатков
        axes[0, 1].hist(residuals, bins=50, alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('Распределение остатков')
        axes[0, 1].set_xlabel('Остатки')
        axes[0, 1].set_ylabel('Частота')
        axes[0, 1].grid(True, alpha=0.3)

        # Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title('Q-Q Plot остатков')
        axes[1, 0].grid(True, alpha=0.3)

        # ACF остатков
        plot_acf(residuals, ax=axes[1, 1], lags=20, alpha=0.05)
        axes[1, 1].set_title('ACF остатков')
        axes[1, 1].set_xlabel('Lag')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        return residuals, residuals_stats

    def plot_future_forecast(self, stationary_series, future_forecast, future_ci, steps=30):
        """
        Визуализация прогноза на будущие периоды.

        Args:
            stationary_series: стационарный ряд с логарифмическими изменениями
            future_forecast: прогнозные значения
            future_ci: доверительные интервалы
            steps: количество шагов прогноза
        """
        plt.figure(figsize=(12, 6))

        # Исторические логарифмические изменения (последние 100 точек)
        if len(stationary_series) > 100:
            historical_data = stationary_series.iloc[-100:]
        else:
            historical_data = stationary_series

        # Создаем индекс для исторических данных
        historical_index = range(len(historical_data))

        plt.plot(historical_index, historical_data.values,
                label='Исторические лог. изменения', color='green', alpha=0.7)

        # Будущий прогноз
        future_index = range(len(historical_data), len(historical_data) + len(future_forecast))

        plt.plot(future_index, future_forecast,
                label='Прогноз лог. изменений', color='red', linewidth=2)

        # Доверительные интервалы
        plt.fill_between(
            future_index,
            future_ci.iloc[:, 0],
            future_ci.iloc[:, 1],
            color='red', alpha=0.2, label='95% Доверительный интервал'
        )

        plt.title('Прогноз логарифмических изменений цены Bitcoin на будущие периоды')
        plt.xlabel('Временной индекс')
        plt.ylabel('Логарифмические изменения')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()


def run_arima_analysis(stationary_series, df_prepared):
    """
    Основная функция для запуска полного анализа ARIMA.

    Args:
        stationary_series: стационарный временной ряд (логарифмические изменения)
        df_prepared: подготовленный DataFrame с датами

    Returns:
        tuple: arima_model, metrics, future_forecast
    """
    # Отключение предупреждений
    warnings.filterwarnings("ignore")

    # Создание экземпляра модели
    arima_model = ARIMAModel()

    # Анализ ACF/PACF для определения параметров
    arima_model.analyze_acf_pacf(stationary_series)

    # Разделение данных
    print("=" * 70)
    print("РАЗДЕЛЕНИЕ ДАННЫХ")
    print("=" * 70)
    train_data, test_data = arima_model.split_data(stationary_series, test_size=0.2)

    # Grid search для поиска лучших параметров
    print("=" * 70)
    print("ПОИСК ЛУЧШИХ ПАРАМЕТРОВ ARIMA")
    print("=" * 70)
    p_range = range(0, 4)
    d_range = range(0, 2)
    q_range = range(0, 4)

    results_df, best_order = arima_model.grid_search_arima(
        train_data, p_range, d_range, q_range
    )

    # Обучение модели с лучшими параметрами
    print("=" * 70)
    print("ОБУЧЕНИЕ МОДЕЛИ С ЛУЧШИМИ ПАРАМЕТРАМИ")
    print("=" * 70)
    arima_model.fit_arima_model(train_data, order=best_order)

    # Оценка модели
    print("=" * 70)
    print("ОЦЕНКА МОДЕЛИ НА ТЕСТОВЫХ ДАННЫХ")
    print("=" * 70)
    predictions, confidence_intervals, metrics = arima_model.evaluate_model(test_data)

    # Визуализация результатов
    print("=" * 70)
    print("ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ")
    print("=" * 70)
    arima_model.plot_results(train_data, test_data, predictions, confidence_intervals)

    # Анализ остатков
    print("=" * 70)
    print("АНАЛИЗ ОСТАТКОВ МОДЕЛИ")
    print("=" * 70)
    arima_model.get_residuals_analysis()

    # Прогноз на будущее
    print("=" * 70)
    print("ПРОГНОЗ НА БУДУЩИЕ ПЕРИОДЫ")
    print("=" * 70)
    last_date = df_prepared.iloc[-1]
    future_forecast, future_ci = arima_model.forecast_future(
        steps=30, last_date=last_date
    )

    # Визуализация будущего прогноза
    arima_model.plot_future_forecast(stationary_series, future_forecast, future_ci)

    # Вывод summary модели
    print("=" * 70)
    print("SUMMARY МОДЕЛИ")
    print("=" * 70)
    print(arima_model.get_model_summary())

    return arima_model, metrics, future_forecast


def quick_arima_test(stationary_series, df_prepared, order=(1, 0, 1)):
    """
    Быстрое тестирование модели ARIMA с заданными параметрами.

    Args:
        stationary_series: стационарный временной ряд
        df_prepared: подготовленный DataFrame с датами
        order: параметры ARIMA модели

    Returns:
        tuple: model, metrics
    """
    warnings.filterwarnings("ignore")

    print("БЫСТРОЕ ТЕСТИРОВАНИЕ ARIMA")
    print("=" * 50)

    model = ARIMAModel()
    train_data, test_data = model.split_data(stationary_series, test_size=0.2)
    model.fit_arima_model(train_data, order=order)
    predictions, confidence_intervals, metrics = model.evaluate_model(test_data)
    model.plot_results(train_data, test_data, predictions, confidence_intervals)

    return model, metrics
