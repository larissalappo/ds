import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_histogram(data: pd.Series, title: str, xlabel: str, ylabel: str, bins: int = 30):
    """Создание гистограммы."""
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_predictions(y_true: pd.Series, y_pred: pd.Series, num_points: int = 20):
    """Визуализация истинных и предсказанных значений."""
    plt.figure(figsize=(12, 6))
    plt.scatter(range(num_points), y_true[:num_points], color='blue', label='Истинные значения', alpha=0.7)
    plt.scatter(range(num_points), y_pred[:num_points], color='red', label='Предсказанные значения', alpha=0.7)
    plt.xlabel('Индекс наблюдения')
    plt.ylabel('Кредитный лимит')
    plt.title('Истинные и предсказанные значения кредитного лимита')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_residuals(y_true: pd.Series, y_pred: pd.Series):
    """Визуализация остатков регрессии."""
    residuals = y_true - y_pred
    
    plt.figure(figsize=(10, 5))
    plt.scatter(y_pred, residuals, alpha=0.7, color='green')
    plt.axhline(y=0, color='red', linestyle='--', linewidth=2)
    plt.xlabel('Предсказанные значения')
    plt.ylabel('Остатки')
    plt.title('Остатки линейной регрессии')
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_feature_importance(coefficients_df: pd.DataFrame, title: str = "Важность признаков"):
    """Визуализация важности признаков по коэффициентам."""
    plt.figure(figsize=(12, 8))
    
    # Берем топ-10 признаков
    top_features = coefficients_df.head(10)
    
    colors = ['red' if coef < 0 else 'blue' for coef in top_features['coefficient']]
    
    plt.barh(top_features['feature'], top_features['coefficient'], color=colors)
    plt.xlabel('Коэффициент')
    plt.ylabel('Признак')
    plt.title(title)
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.show()

def plot_correlation_with_target(df: pd.DataFrame, target_column: str = 'Credit_Limit'):
    """Визуализация корреляции признаков с целевой переменной."""
    if target_column not in df.columns:
        print(f"Целевая переменная {target_column} не найдена")
        return
    
    # Выбираем только числовые колонки
    numeric_columns = df.select_dtypes(include=['number']).columns
    
    if len(numeric_columns) < 2:
        print("Недостаточно числовых колонок для анализа корреляции")
        return
    
    # Вычисляем корреляцию с целевой переменной
    correlations = df[numeric_columns].corr()[target_column].drop(target_column)
    correlations = correlations.sort_values(key=abs, ascending=False)
    
    # Берем топ-15 признаков по абсолютной корреляции
    top_correlations = correlations.head(15)
    
    plt.figure(figsize=(12, 10))
    colors = ['red' if x < 0 else 'blue' for x in top_correlations.values]
    
    bars = plt.barh(top_correlations.index, top_correlations.values, color=colors, alpha=0.7)
    plt.xlabel('Коэффициент корреляции', fontsize=12)
    plt.ylabel('Признаки', fontsize=12)
    plt.title(f'Корреляция признаков с {target_column}', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='x')
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.8)
    
    # Добавляем значения на график
    for i, (feature, value) in enumerate(zip(top_correlations.index, top_correlations.values)):
        plt.text(value, i, f'{value:.3f}', ha='left' if value >= 0 else 'right', 
                va='center', fontweight='bold', fontsize=10)
    
    # Добавляем легенду для цветов
    plt.text(0.02, 0.98, 'Положительная корреляция', transform=plt.gca().transAxes, 
             color='blue', fontweight='bold', fontsize=10, verticalalignment='top')
    plt.text(0.02, 0.94, 'Отрицательная корреляция', transform=plt.gca().transAxes, 
             color='red', fontweight='bold', fontsize=10, verticalalignment='top')
    
    plt.tight_layout()
    plt.show()
    
    # Выводим численные значения корреляции
    print("\nТоп-10 признаков по корреляции с Credit_Limit:")
    print("=" * 60)
    for i, (feature, corr) in enumerate(top_correlations.head(10).items(), 1):
        print(f"{i:2d}. {feature:25s}: {corr:7.3f}")