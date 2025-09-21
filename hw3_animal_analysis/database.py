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
            print(f"Всего записей в представлении {view_name}: {pd.read_sql_query(f'SELECT COUNT(*) FROM {view_name}', conn).iloc[0,0]}")
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

        # Создаем сырые таблицы
        print("Сохраняем raw_intake...")
        intake_df.to_sql('raw_intake', conn, if_exists='replace', index=False)
        print("Сохраняем raw_outcome...")
        outcome_df.to_sql('raw_outcome', conn, if_exists='replace', index=False)

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
        print("Выбираем уникальные animal_id из raw_intake и raw_outcome и к ним присоединяем данные о name, animal_type, breed, color из raw_outcome, если есть, иначе - из raw_intake")
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS unique_animals AS
        SELECT 
            intake.animal_id,
            COALESCE(out.name, intake.name) AS name,
            COALESCE(out.animal_type, intake.animal_type) AS animal_type,
            COALESCE(out.breed, intake.breed) AS breed,
            COALESCE(out.color, intake.color) AS color
        FROM 
            raw_intake intake
        LEFT JOIN 
            raw_outcome out ON intake.animal_id = out.animal_id
        UNION
        SELECT 
            out.animal_id,
            out.name,
            out.animal_type,
            out.breed,
            out.color
        FROM 
            raw_outcome out
        LEFT JOIN 
            raw_intake intake ON out.animal_id = intake.animal_id
        WHERE 
            intake.animal_id IS NULL
        ''')

        conn.commit()
        print("Временное представленияе создано успешно")

        print()
        print_view_sample(conn, 'unique_animals')

    except Exception as e:
        print(f"❌ Ошибка при создании временных представлений: {e}")
        raise
    finally:
        conn.close()

def analyze_raw_data():
    """Анализ сырых данных перед обработкой"""
    print("\nАнализируем данные в представлениях")

    conn = sqlite3.connect('animal_shelter.db')

    try:
        print("\nПроверяем, что у нас не размножились записи при формировании unique_animals")
        unique_animal_id = pd.read_sql_query('WITH s1 as (SELECT animal_id FROM raw_outcome UNION SELECT animal_id FROM raw_intake) SELECT count(animal_id) from s1', conn).iloc[0,0]
        unique_animals_records_count = pd.read_sql_query(f'SELECT COUNT(*) FROM unique_animals', conn).iloc[0,0] 
        if unique_animal_id == unique_animals_records_count:
            print("Всего уникальных animal_id в raw_intake и raw_outcome:", unique_animal_id, "что равно количеству записей в unique_animals")
        else:
            ("Что-то пошло не так. Всего уникальных animal_id в raw_intake и raw_outcome: ", unique_animal_id, "что не равно количеству записей в unique_animals")

        print("\nМожно сделать еще много разных представлений и запросов, но в DBeaver это делать удобнее\n")


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
        WITH intake_dates AS (
            SELECT 
                animal_id,
                datetime,
                ROW_NUMBER() OVER (PARTITION BY animal_id ORDER BY datetime) AS rn
            FROM 
                raw_intake
        ),
        outcome_dates AS (
            SELECT 
                out.animal_id,
                out.datetime AS outcome_datetime,
                out.outcome_type,
                out.outcome_subtype,
                intake.datetime AS intake_datetime,
                ROW_NUMBER() OVER (PARTITION BY out.animal_id ORDER BY out.datetime) AS rn
            FROM 
                raw_outcome out
            LEFT JOIN intake_dates intake ON out.animal_id = intake.animal_id
            WHERE intake.datetime IS NOT NULL
        )
        SELECT
            animal_id,
            outcome_datetime,
            outcome_type,
            outcome_subtype,
            CASE
                WHEN intake_datetime IS NOT NULL AND outcome_datetime IS NOT NULL THEN
                    julianday(outcome_datetime) - julianday(intake_datetime)
                ELSE
                    NULL
            END AS days_in_shelter
        FROM 
            outcome_dates
        WHERE 
            rn = 1
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
        views = ['unique_animals']
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

        print("""\nТаблицу outcome обогатили полем days_in_shelter, которое рассчитали как разницу между raw_outcome.datetime и raw_intake.datetime, связав по animal_id.
             Учтено, что может быть несколько записей по одному animal_id в каждой из raw_outcome и raw_intake - берем ближайшую следующую raw_outcome.datetime для каждой raw_intake.datetime. 
             Также учтено, что может быть не заполнено какое-то из raw_outcome.datetime или raw_intake.datetime или оба - тогда days_in_shelter is null.
             При оптимизации запроса использованы CTE (with) и оконная функция ROW_NUMBER()
             """)

    except Exception as e:
        print(f"❌ Ошибка при выводе структуры: {e}")
        raise
    finally:
        conn.close()
