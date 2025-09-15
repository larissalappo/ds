import data_loader
import data_processing
import ml_module
import visualization
import pandas as pd
import numpy as np

def main():
    print("ПРОГНОЗИРОВАНИЕ КРЕДИТНОГО ЛИМИТА")
    print("=" * 60)
    
    # Загрузка данных
    df = data_loader.load_credit_card_data('D:/GIT/ds/hw2/BankChurners.csv')
    
    # Удаляем колонки, которые в описании датасета рекрмендуют удалить до исследования (не будем их визуализировать даже для анализа)
    cols_to_drop = [
        'Naive_Bayes_Classifier_Attrition_Flag_Card_Category_Contacts_Count_12_mon_Dependent_count_Education_Level_Months_Inactive_12_mon_1',
        'Naive_Bayes_Classifier_Attrition_Flag_Card_Category_Contacts_Count_12_mon_Dependent_count_Education_Level_Months_Inactive_12_mon_2',
    ]
    for col in cols_to_drop:
        if col in df.columns:
            df.drop(col, axis=1, inplace=True)
            print(f"Удален столбец: {col}")
    
    if df is None:
        print("Скачайте датасет: https://www.kaggle.com/datasets/sakshigoyal7/credit-card-customers")
        return
    
    # Исследование данных
    data_processing.explore_data(df)
    
    # Анализ корреляции перед обработкой
    print("\nАНАЛИЗ КОРРЕЛЯЦИИ С CREDIT_LIMIT:")
    print("=" * 60)
    
    # Построим график корреляции с целевой переменной
    visualization.plot_correlation_with_target(df, 'Credit_Limit')
    
    # Подготовка данных

    X, y = data_processing.prepare_data(df)
    
    if X is None or y is None:
        return
    
    # Визуализация целевой переменной
    visualization.plot_histogram(y, 'Распределение кредитного лимита', 'Кредитный лимит', 'Частота')
    
    # Разделение данных
    X_train, X_test, y_train, y_test = ml_module.split_data(X, y)
    
    # Масштабирование признаков
    X_train_scaled, X_test_scaled, scaler = ml_module.scale_features(X_train, X_test)
    
    # Обучение модели
    print()
    print('=' * 60)
    print("Обучение линейной регрессии...")
    model = ml_module.train_linear_regression(X_train_scaled, y_train)
    print('=' * 60)
    print()

    # Предсказание
    y_pred = ml_module.predict(model, X_test_scaled)
    
    # Оценка модели
    metrics = ml_module.evaluate_model(y_test, y_pred)
    
    # Коэффициенты модели
    coefficients = ml_module.get_coefficients(model, X.columns.tolist())
    ml_module.print_coefficients(coefficients)
    
    # Визуализация
    visualization.plot_predictions(y_test, y_pred)
    visualization.plot_residuals(y_test, y_pred)
    visualization.plot_feature_importance(coefficients, "Важность признаков для кредитного лимита")
    
    print("Анализ завершен!")

if __name__ == "__main__":
    main()