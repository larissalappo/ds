import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import pandas as pd
import numpy as np

def execute_queries():
    """Сложные SQL-запросы с JOIN"""

    conn = sqlite3.connect('animal_shelter.db')

    try:
        print("=" * 60)
        print("\n1. Количество животных по типам:")
        query = '''
        SELECT at.animal_type, COUNT(*) as count
        FROM animals a
        JOIN animal_types at ON a.animal_type_id = at.type_id
        GROUP BY at.animal_type
        ORDER BY count DESC
        '''
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))

        print("=" * 60)
        print("\n2. Top 10 самых распространенных пород:")
        query = '''
        SELECT b.breed_name, COUNT(*) as count
        FROM animals a
        JOIN breeds b ON a.breed_id = b.breed_id
        GROUP BY b.breed_name
        ORDER BY count DESC
        LIMIT 10
        '''
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))

        print("=" * 60)
        print("\n3. Статистика по выходу из приюта (outcome types):")
        query = '''
        SELECT outcome_type, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM outcome), 2) as percentage
        FROM outcome
        GROUP BY outcome_type
        ORDER BY count DESC
        '''
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))

        print("=" * 60)
        print("\n4. Среднее время пребывания в приюте по типам животных:")
        query = '''
        SELECT at.animal_type,
               ROUND(AVG(o.days_in_shelter), 2) as avg_days
        FROM outcome o
        JOIN animals a ON o.animal_id = a.animal_id
        JOIN animal_types at ON a.animal_type_id = at.type_id
        WHERE o.days_in_shelter IS NOT NULL
        GROUP BY at.animal_type
        ORDER BY avg_days DESC
        '''
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))

        print("=" * 60)
        print("\n5. Статистика по месяцам поступлений:")
        query = '''
        SELECT
            strftime('%Y-%m', intake_date) as month,
            COUNT(*) as count
        FROM intake
        WHERE intake_date IS NOT NULL
        GROUP BY month
        ORDER BY month
        LIMIT 24
        '''
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))

    except Exception as e:
        print(f"❌ Ошибка при выполнении запросов: {e}")
        raise
    finally:
        conn.close()

def create_visualizations():
    """Визуализация данных из нормализованной БД"""

    conn = sqlite3.connect('animal_shelter.db')

    try:
        # Распределение по типам животных
        print()
        print()
        print()
        query = '''
        SELECT at.animal_type, COUNT(*) as count
        FROM animals a
        JOIN animal_types at ON a.animal_type_id = at.type_id
        GROUP BY at.animal_type
        '''
        df = pd.read_sql_query(query, conn)

        plt.figure(figsize=(12, 6))
        bars = plt.bar(df['animal_type'], df['count'])
        plt.title('Распределение животных по типам в приюте', fontsize=16, fontweight='bold')
        plt.xlabel('Тип животного', fontsize=12)
        plt.ylabel('Количество', fontsize=12)
        plt.xticks(rotation=45, ha='right')

        # Добавляем значения на столбцы
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{int(height)}', ha='center', va='bottom')

        plt.tight_layout()
        plt.show()

        # Выходы из приюта (круговая диаграмма)
        print()
        print()
        print()
        query = "SELECT outcome_type, COUNT(*) as count FROM outcome GROUP BY outcome_type"
        df = pd.read_sql_query(query, conn)

        plt.figure(figsize=(10, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(df)))
        wedges, texts, autotexts = plt.pie(df['count'], labels=df['outcome_type'], autopct='%1.1f%%',
                                          colors=colors, startangle=90)
        plt.title('Распределение выходов из приюта', fontsize=16, fontweight='bold')
        plt.axis('equal')
        plt.show()

        # Время пребывания в приюте
        print()
        print()
        print()
        query = '''
        SELECT at.animal_type, AVG(o.days_in_shelter) as avg_days
        FROM outcome o
        JOIN animals a ON o.animal_id = a.animal_id
        JOIN animal_types at ON a.animal_type_id = at.type_id
        WHERE o.days_in_shelter IS NOT NULL
        GROUP BY at.animal_type
        '''
        df = pd.read_sql_query(query, conn)

        plt.figure(figsize=(12, 6))
        bars = plt.bar(df['animal_type'], df['avg_days'])
        plt.title('Среднее время пребывания в приюте по типам животных', fontsize=16, fontweight='bold')
        plt.xlabel('Тип животного', fontsize=12)
        plt.ylabel('Среднее количество дней', fontsize=12)
        plt.xticks(rotation=45, ha='right')

        # Добавляем значения на столбцы
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom')

        plt.tight_layout()
        plt.show()

        # Типы поступлений в приют
        print()
        print()
        print()
        query = "SELECT intake_type, COUNT(*) as count FROM intake GROUP BY intake_type"
        df = pd.read_sql_query(query, conn)

        plt.figure(figsize=(10, 6))
        bars = plt.bar(df['intake_type'], df['count'])
        plt.title('Типы поступлений в приют', fontsize=16, fontweight='bold')
        plt.xlabel('Тип поступления', fontsize=12)
        plt.ylabel('Количество', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

        # Динамика поступлений по месяцам
        print()
        print()
        print()
        query = '''
        SELECT
            strftime('%Y-%m', intake_date) as month,
            COUNT(*) as count
        FROM intake
        WHERE intake_date IS NOT NULL
        GROUP BY month
        ORDER BY month
        '''
        df = pd.read_sql_query(query, conn)

        plt.figure(figsize=(14, 6))
        plt.plot(df['month'], df['count'], marker='o', linewidth=2, markersize=6)
        plt.title('Динамика поступлений животных по месяцам', fontsize=16, fontweight='bold')
        plt.xlabel('Месяц', fontsize=12)
        plt.ylabel('Количество поступлений', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        print("Визуализации созданы успешно!")

    except Exception as e:
        print(f"❌ Ошибка при создании визуализаций: {e}")
        raise
    finally:
        conn.close()

def perform_additional_analysis():
    """Дополнительный анализ данных"""
    print("Дополнительный анализ данных")

    conn = sqlite3.connect('animal_shelter.db')

    try:
        # Анализ сезонности поступлений
        print("=" * 60)
        print("Анализ сезонности поступлений:")
        season_query = '''
        SELECT
            CASE
                WHEN strftime('%m', intake_date) IN ('12', '01', '02') THEN 'Зима'
                WHEN strftime('%m', intake_date) IN ('03', '04', '05') THEN 'Весна'
                WHEN strftime('%m', intake_date) IN ('06', '07', '08') THEN 'Лето'
                WHEN strftime('%m', intake_date) IN ('09', '10', '11') THEN 'Осень'
            END as season,
            COUNT(*) as count
        FROM intake
        WHERE intake_date IS NOT NULL
        GROUP BY season
        ORDER BY count DESC
        '''
        season_df = pd.read_sql_query(season_query, conn)
        print(season_df.to_string(index=False))

        # Анализ по времени суток
        print("=" * 60)
        print("\nАнализ по времени суток:")
        time_query = '''
        SELECT
            CASE
                WHEN CAST(strftime('%H', intake_date) AS INTEGER) BETWEEN 6 AND 11 THEN 'Утро (6-12)'
                WHEN CAST(strftime('%H', intake_date) AS INTEGER) BETWEEN 12 AND 17 THEN 'День (12-18)'
                WHEN CAST(strftime('%H', intake_date) AS INTEGER) BETWEEN 18 AND 23 THEN 'Вечер (18-24)'
                ELSE 'Ночь (0-6)'
            END as time_of_day,
            COUNT(*) as count
        FROM intake
        WHERE intake_date IS NOT NULL
        GROUP BY time_of_day
        ORDER BY count DESC
        '''
        time_df = pd.read_sql_query(time_query, conn)
        print(time_df.to_string(index=False))

        # Статистика по условиям поступления
        print("=" * 60)
        print("\nСтатистика по условиям поступления:")
        condition_query = '''
        SELECT
            intake_condition,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM intake), 2) as percentage
        FROM intake
        GROUP BY intake_condition
        ORDER BY count DESC
        '''
        condition_df = pd.read_sql_query(condition_query, conn)
        print(condition_df.to_string(index=False))

        print("=" * 60)
        print("\nЖивотные с несколькими поступлениями:")
        query = '''
        WITH intake_counts AS (
            SELECT
                animal_id,
                COUNT(*) as intake_count,
                MIN(intake_date) as first_intake,
                MAX(intake_date) as last_intake
            FROM intake
            GROUP BY animal_id
            HAVING COUNT(*) > 1
            ORDER BY intake_count DESC
        )
        SELECT
            ic.animal_id,
            a.name,
            ic.intake_count,
            strftime('%d.%m.%Y %H:%M', ic.first_intake) as first_intake,
            strftime('%d.%m.%Y %H:%M', ic.last_intake) as last_intake,
            cast(JULIANDAY(ic.last_intake) - JULIANDAY(ic.first_intake) as integer) as days_between_first_last
        FROM intake_counts ic
        JOIN animals a ON ic.animal_id = a.animal_id
        ORDER BY ic.intake_count DESC
        LIMIT 15
        '''
        df_multiple_intakes = pd.read_sql_query(query, conn)
        print(df_multiple_intakes.to_string(index=False))


    except Exception as e:
        print(f"❌ Ошибка при дополнительном анализе: {e}")
    finally:
        conn.close()

