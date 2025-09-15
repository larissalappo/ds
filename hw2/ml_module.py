import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42):
    """Разделение данных на тренировочную и тестовую выборки."""
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """Масштабирование признаков."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler

def train_linear_regression(X_train: pd.DataFrame, y_train: pd.Series):
    """Обучение модели линейной регрессии."""
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def predict(model, X: pd.DataFrame):
    """Предсказание на новых данных."""
    return model.predict(X)

def evaluate_model(y_true: pd.Series, y_pred: pd.Series):
    """Оценка модели линейной регрессии."""
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print("=== Оценка линейной регрессии ===")
    print(f"Среднеквадратичная ошибка (MSE): {mse:.2f}")
    print(f"Корень из MSE (RMSE): {rmse:.2f}")
    print(f"Средняя абсолютная ошибка (MAE): {mae:.2f}")
    print(f"Коэффициент детерминации R²: {r2:.4f}")
    print("=" * 60)
    
    return {'mse': mse, 'rmse': rmse, 'mae': mae, 'r2': r2}

def get_coefficients(model, feature_names: list) -> pd.DataFrame:
    """Получение коэффициентов линейной регрессии."""
    coefficients = pd.DataFrame({
        'feature': feature_names,
        'coefficient': model.coef_
    }).sort_values('coefficient', key=abs, ascending=False)
    
    return coefficients

def print_coefficients(coefficients_df: pd.DataFrame):
    """Вывод коэффициентов модели."""
    print("======== Коэффициенты линейной регрессии ===================")
    for i, (_, row) in enumerate(coefficients_df.iterrows()):
        print(f"{i+1:2d}. {row['feature']:25s}: {row['coefficient']:10.4f}")
    print("=" * 60)