import sqlite3 as sq
from contextlib import contextmanager
import numpy as np

data_b = "data_products.db"

@contextmanager
def get_connection(data_base):
    conn = None
    try:
        conn = sq.connect(data_base)
        yield conn
        conn.commit()
    except sq.Error as e:
        if conn:
            conn.rollback()
        print("Не корректный путь к базе :( ")
        raise
    finally:
        if conn:
            conn.close()

def check_tables(data_base):
    with get_connection(data_base) as conn:
        cursor = conn.cursor()
        # Таблица категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,  -- добавил UNIQUE
            description TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
        ''')

        # Таблица товаров
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            typical_price REAL NOT NULL CHECK(typical_price > 0),
            unit TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id))
        ''')

        # Таблица списков
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_lists(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME)
        ''')

        # Таблица элементов списка
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS list_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL CHECK(quantity > 0),
            is_bought BOOLEAN DEFAULT 0,
            price_at_purchase REAL,  -- теперь может быть NULL
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE)
        ''')

        # Таблица истории покупок
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            list_id INTEGER NOT NULL,
            quantity REAL NOT NULL CHECK(quantity > 0),
            price REAL NOT NULL CHECK(price >= 0),
            total REAL NOT NULL CHECK(total >= 0),
            purchased_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE)
        ''')
def check_data_in_tables(data_base):
    with get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM categories')
        count = cursor.fetchone()[0]
        if count == 0:
            categories = [("Молочные продукты", "Молоко, сыр, йогурт, творог"),
                ("Овощи и фрукты", "Свежие овощи и фрукты"),
                ("Мясо и рыба", "Мясо, птица, рыба, морепродукты"),
                ("Бакалея", "Крупы, макароны, масло, консервы"),
                ("Напитки", "Вода, соки, газировка"),
                ("Хлебобулочные изделия", "Хлеб, булочки, выпечка"),
                ("Бытовая химия", "Моющие средства, порошки")
                ]
            cursor.executemany("INSERT INTO categories (name, description) VALUES (?,?)", categories)
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("SELECT id, name FROM categories")
            cat_dict = {name: id for id, name in cursor.fetchall()}
            products = [("Молоко", cat_dict.get("Молочные продукты"), 80.0, "литр"),
                ("Хлеб", cat_dict.get("Хлебобулочные изделия"), 45.0, "шт"),
                ("Яйца", cat_dict.get("Молочные продукты"), 90.0, "десяток"),
                ("Яблоки", cat_dict.get("Овощи и фрукты"), 120.0, "кг"),
                ("Курица", cat_dict.get("Мясо и рыба"), 350.0, "кг")]
            cursor.executemany("INSERT INTO products (name , category_id, typical_price, unit) VALUES (?,?,?,?)", products)
    print("Базовые категорий и продукты были созданы")
    return 0

def init_datavase(data_base):
    check_tables(data_base)
    check_data_in_tables(data_base)
    print('Таблицы и стандартные категорий и продукты были готовы')
    return 0

init_datavase(data_b)