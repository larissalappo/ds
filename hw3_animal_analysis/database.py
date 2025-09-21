import sqlite3
import pandas as pd
import os

def delete_existing_database():
    """Удаление существующей базы данных, если она есть"""
    print("Проверяем существующую базу данных...")
    if os.path.exists('animal_shelter.db'):
        os.remove('animal_shelter.db')
        print("Существующая база данных удалена")
    else:
        print("База данных не существует, создаем новую")

def print_table_sample(conn, table_name, limit=20):
    """Вывод sample данных из таблицы"""
    print(f"\nСодержимое таблицы {table_name} (первые {limit} записей):")
    print("-" * 60)
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        if len(df) > 0:
            print(df.to_string(index=False))
            print(f"Всего записей в таблице: {pd.read_sql_query(f'SELECT COUNT(*) FROM {table_name}', conn).iloc[0,0]}")
        else:
            print("Таблица пуста")
    except Exception as e:
        print(f"❌ Ошибка при чтении таблицы {table_name}: {e}")

def print_view_sample(conn, view_name, limit=20):
    """Вывод sample данных из view"""
    print(f"\nСодержимое view {view_name} (первые {limit} записей):")
    print("-" * 60)
    try:
        query = f"SELECT * FROM {view_name} LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        if len(df) > 0:
            print(df.to_string(index=False))
            print(f"Всего записей в view: {pd.read_sql_query(f'SELECT COUNT(*) FROM {view_name}', conn).iloc[0,0]}")
        else:
            print("Представление пустое")
    except Exception as e:
        print(f"Ошибка при чтении view {view_name}: {e}")

def create_raw_tables():
    """Создание сырых таблиц - копий CSV файлов"""
    print("\nЗагружаем CSV файлы в сырые таблицы...")

    conn = sqlite3.connect('animal_shelter.db')

    try:
        # Загрузка данных в сырые таблицы
        print("Загружаем aac_intakes.csv...")
        intake_df = pd.read_csv('data/aac_intakes.csv')
        print("Загружаем aac_outcomes.csv...")
        outcome_df = pd.read_csv('data/aac_outcomes.csv')
        print("Загружаем aac_intakes_outcomes.csv...")
        intake_outcome_df = pd.read_csv('data/aac_intakes_outcomes.csv')

        # Создаем сырые таблицы
        print("Сохраняем raw_intake...")
        intake_df.to_sql('raw_intake', conn, if_exists='replace', index=False)
        print("Сохраняем raw_outcome...")
        outcome_df.to_sql('raw_outcome', conn, if_exists='replace', index=False)
        print("Сохраняем raw_intake_outcome...")
        intake_outcome_df.to_sql('raw_intake_outcome', conn, if_exists='replace', index=False)

        print("Сырые таблицы созданы успешно")
        print()

        print_table_sample(conn, 'raw_intake')
        print_table_sample(conn, 'raw_outcome')

    except Exception as e:
        print(f"❌ Ошибка при создании сырых таблиц: {e}")
        raise
    finally:
        conn.close()

def create_temp_views():
    """Создание временных представлений для анализа"""
    print("\nСоздаем временные представления для анализа...")

    conn = sqlite3.connect('animal_shelter.db')
    cursor = conn.cursor()

    try:
        # Временное представление для уникальных животных
        print("Создаем представление unique_animals...")
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS unique_animals AS
        SELECT DISTINCT
            animal_id,
            name,
            animal_type,
            breed,
            color
        FROM (
            SELECT animal_id, name, animal_type, breed, color FROM raw_intake
            UNION
            SELECT animal_id, name, animal_type, breed, color FROM raw_outcome
             )
        ''')

        # Временное представление для статистики типов животных
        print("Создаем представление animal_type_stats...")
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS animal_type_stats AS
        SELECT
            animal_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM unique_animals), 2) as percentage
        FROM unique_animals
        GROUP BY animal_type
        ORDER BY count DESC
        ''')

        # Временное представление для статистики пород
        print("Создаем представление breed_stats...")
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS breed_stats AS
        SELECT
            breed,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM unique_animals), 2) as percentage
        FROM unique_animals
        GROUP BY breed
        ORDER BY count DESC
        ''')

        conn.commit()
        print("Временные представления созданы успешно")

        # Выводим sample данных из представлений
        print_table_sample(conn, 'unique_animals')
        print_table_sample(conn, 'animal_type_stats')
        print_table_sample(conn, 'breed_stats')

    except Exception as e:
        print(f"❌ Ошибка при создании временных представлений: {e}")
        raise
    finally:
        conn.close()

def analyze_raw_data():
    """Анализ сырых данных перед обработкой"""
    print("\nАнализируем сырые данные...")

    conn = sqlite3.connect('animal_shelter.db')

    try:
        # Основная статистика
        print("Основная статистика:")
        intake_count = pd.read_sql_query("SELECT COUNT(*) FROM raw_intake", conn).iloc[0,0]
        outcome_count = pd.read_sql_query("SELECT COUNT(*) FROM raw_outcome", conn).iloc[0,0]
        unique_animals_count = pd.read_sql_query("SELECT COUNT(*) FROM unique_animals", conn).iloc[0,0]

        print(f"   Поступления (intake): {intake_count} записей")
        print(f"   Исходы (outcome): {outcome_count} записей")
        print(f"   Уникальных животных: {unique_animals_count}")

        # Статистика по типам животных
        print("\nРаспределение по типам животных:")
        type_stats = pd.read_sql_query("SELECT * FROM animal_type_stats", conn)
        for _, row in type_stats.iterrows():
            print(f"   {row['animal_type']}: {row['count']} ({row['percentage']}%)")

        # Топ-5 пород
        print("\nТоп-5 пород:")
        breed_stats = pd.read_sql_query("SELECT * FROM breed_stats LIMIT 5", conn)
        for _, row in breed_stats.iterrows():
            print(f"   {row['breed']}: {row['count']} ({row['percentage']}%)")

    except Exception as e:
        print(f"❌ Ошибка при анализе данных: {e}")
        raise
    finally:
        conn.close()

def create_normalized_tables():
    """Создание нормализованных таблиц со справочниками"""
    print("\nСоздаем нормализованную структуру...")

    conn = sqlite3.connect('animal_shelter.db')
    cursor = conn.cursor()

    try:
        # 1. Создаем справочник типов животных
        print("Создаем сравочник animal_types...")
        cursor.execute('''
        CREATE TABLE animal_types (
            type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_type TEXT UNIQUE NOT NULL
        )
        ''')

        cursor.execute('''
        INSERT OR IGNORE INTO animal_types (animal_type)
        SELECT DISTINCT animal_type FROM (
            SELECT animal_type FROM raw_intake
            UNION
            SELECT animal_type FROM raw_outcome
        )
        ''')
        print(f"   Добавлено записей: {cursor.rowcount}")

        # 2. Создаем справочник окрасов
        print("Создаем справочник colors...")
        cursor.execute('''
        CREATE TABLE colors (
            color_id INTEGER PRIMARY KEY AUTOINCREMENT,
            color_name TEXT UNIQUE NOT NULL
        )
        ''')

        cursor.execute('''
        INSERT OR IGNORE INTO colors (color_name)
        SELECT DISTINCT color FROM (
            SELECT color FROM raw_intake
            UNION
            SELECT color FROM raw_outcome
        )
        ''')
        print(f"   Добавлено записей: {cursor.rowcount}")

        # 3. Создаем справочник пород
        print("Создаем справочник breeds...")
        cursor.execute('''
        CREATE TABLE breeds (
            breed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            breed_name TEXT UNIQUE NOT NULL
        )
        ''')

        cursor.execute('''
        INSERT OR IGNORE INTO breeds (breed_name)
        SELECT DISTINCT breed FROM (
            SELECT breed FROM raw_intake
            UNION
            SELECT breed FROM raw_outcome
        )
        ''')
        print(f"   Добавлено записей: {cursor.rowcount}")

        # 4. Создаем основную таблицу животных
        print("Создаем таблицу animals...")
        cursor.execute('''
        CREATE TABLE animals (
            animal_id TEXT PRIMARY KEY,
            name TEXT,
            animal_type_id INTEGER,
            breed_id INTEGER,
            color_id INTEGER,
            FOREIGN KEY (animal_type_id) REFERENCES animal_types(type_id),
            FOREIGN KEY (breed_id) REFERENCES breeds(breed_id),
            FOREIGN KEY (color_id) REFERENCES colors(color_id)
        )
        ''')

        # Заполняем таблицу животных
        print("Заполняем таблицу animals...")
        cursor.execute('''
        INSERT OR REPLACE INTO animals (animal_id, name, animal_type_id, breed_id, color_id)
        SELECT
            ua.animal_id,
            ua.name,
            at.type_id,
            b.breed_id,
            c.color_id
        FROM unique_animals ua
        JOIN animal_types at ON ua.animal_type = at.animal_type
        JOIN breeds b ON ua.breed = b.breed_name
        JOIN colors c ON ua.color = c.color_name
        ''')
        print(f"   Добавлено животных: {cursor.rowcount}")

        # 5. Создаем таблицу поступлений
        print("Создаем таблицу intake...")
        cursor.execute('''
        CREATE TABLE intake (
            intake_id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT,
            intake_date TEXT NOT NULL,
            intake_type TEXT,
            intake_condition TEXT,
            found_location TEXT,
            FOREIGN KEY (animal_id) REFERENCES animals(animal_id)
        )
        ''')

        cursor.execute('''
        INSERT INTO intake (animal_id, intake_date, intake_type, intake_condition, found_location)
        SELECT
            animal_id,
            datetime,
            intake_type,
            intake_condition,
            found_location
        FROM raw_intake
        ''')
        print(f"   Добавлено поступлений: {cursor.rowcount}")

        # 6. Создаем таблицу выходов
        print("Создаем таблицу outcome...")
        cursor.execute('''
        CREATE TABLE outcome (
            outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT,
            outcome_date TEXT NOT NULL,
            outcome_type TEXT,
            outcome_subtype TEXT,
            days_in_shelter INTEGER,
            FOREIGN KEY (animal_id) REFERENCES animals(animal_id)
        )
        ''')

        cursor.execute('''
        INSERT INTO outcome (animal_id, outcome_date, outcome_type, outcome_subtype, days_in_shelter)
        SELECT
            raw_outcome.animal_id,
            raw_outcome.datetime,
            raw_outcome.outcome_type,
            raw_outcome.outcome_subtype,
            case when coalesce(raw_outcome.datetime,0) <> 0 and coalesce(raw_intake.datetime,0) <> 0 and coalesce(raw_outcome.datetime,0) > coalesce(raw_intake.datetime,0)
                 then julianday(raw_outcome.datetime) - julianday(raw_intake.datetime)
                 else null
            end
        FROM raw_outcome
        left join raw_intake on raw_outcome.animal_id=raw_intake.animal_id
        ''')
        print(f"   Добавлено выходов: {cursor.rowcount}")

        conn.commit()
        print("Нормализованная структура создана успешно")

    except Exception as e:
        print(f"❌ Ошибка при создании нормализованной структуры: {e}")
        raise
    finally:
        conn.close()

def drop_temp_views():
    """Удаление временных представлений"""
    print("\nУдаляем временные представления...")

    conn = sqlite3.connect('animal_shelter.db')
    cursor = conn.cursor()

    try:
        views = ['unique_animals', 'animal_type_stats', 'breed_stats']
        for view in views:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
            print(f"   Удалено представление: {view}")

        conn.commit()
        print("Временные представления удалены")

    except Exception as e:
        print(f"❌ Ошибка при удалении представлений: {e}")
        raise
    finally:
        conn.close()

def print_database_structure():
    """Вывод структуры базы данных и примеров данных"""

    conn = sqlite3.connect('animal_shelter.db')
    cursor = conn.cursor()

    try:
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        print("Таблицы в базе данных:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   ├─ {table_name}: {count} записей")

        # Статистика по нормализованным таблицам
        print("\nСтатистика нормализованных таблиц:")
        normalized_tables = ['animal_types', 'breeds', 'colors', 'animals', 'intake', 'outcome']

        for table in normalized_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ├─ {table}: {count} записей")

        print_table_sample(conn, 'animal_types')
        print_table_sample(conn, 'breeds')
        print_table_sample(conn, 'colors')
        print_table_sample(conn, 'animals')
        print_table_sample(conn, 'intake')
        print_table_sample(conn, 'outcome')

    except Exception as e:
        print(f"❌ Ошибка при выводе структуры: {e}")
        raise
    finally:
        conn.close()
