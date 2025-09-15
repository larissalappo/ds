import pandas as pd

def load_credit_card_data(file_path: str = 'BankChurners.csv') -> pd.DataFrame:
    """Загрузка данных о клиентах кредитных карт."""
    try:
        df = pd.read_csv(file_path)
        print(f"Данные загружены. Размер: {df.shape}")
        return df
    except FileNotFoundError:
        print(f"Файл {file_path} не найден")
        return None
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return None