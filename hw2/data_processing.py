import pandas as pd
import numpy as np

def explore_data(df: pd.DataFrame):
    """Исследование данных."""
    print("Информация о данных:")
    print(f"Размер: {df.shape}")
    print(f"Колонки: {list(df.columns)}")
    
    print("\nПропущенные значения:")
    print(df.isnull().sum())

def remove_outliers(df, columns, factor=1.5):
    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    return df    

def prepare_data(df: pd.DataFrame) -> tuple:
    """Подготовка данных для линейной регрессии."""
    if df is None:
        return None, None
    
    df_processed = df.copy()
    # Удаляем ненужные колонки из копии, чтобы выводить их при визуализации датасета
    print('=' * 60)
    print('Удаляем ненужные (не используются при анализе) колонки из копии, чтобы выводить их при визуализации датасета')
    print('Удаляем Avg_Open_To_Buy из-за кореляции с Credit_Limit')
    cols_to_drop = [
        'CLIENTNUM', 
        'Attrition_Flag', 
        'Avg_Open_To_Buy'  # Добавляем удаление этого столбца из-за кореляции с Credit_Limit
    ]
    
    for col in cols_to_drop:
        if col in df_processed.columns:
            df_processed.drop(col, axis=1, inplace=True)
            print(f"Удален столбец: {col}")
    
    # Удаляем выбросы
    print("=" * 60)
    print('Удаляем выбросы по Credit_Limit, Avg_Utilization_Ratio, Total_Revolving_Bal, Total_Trans_Amt, Total_Trans_Ct')
    df_processed = remove_outliers(df_processed, ['Credit_Limit', 'Avg_Utilization_Ratio', 'Total_Revolving_Bal', 'Total_Trans_Amt', 'Total_Trans_Ct'])
    
    # Кодируем категориальные переменные
    categorical_cols = ['Gender', 'Education_Level', 'Marital_Status', 'Income_Category', 'Card_Category']
    
    for col in categorical_cols:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].astype('category').cat.codes
    
    # Убедимся, что целевая переменная существует
    if 'Credit_Limit' not in df_processed.columns:
        print("Целевая переменная Credit_Limit не найдена")
        return None, None
    
    # Разделяем на признаки и целевую переменную
    X = df_processed.drop('Credit_Limit', axis=1)
    y = df_processed['Credit_Limit']
      
    print(f"Признаки: {X.shape}, Целевая: {y.shape}")
    return X, y