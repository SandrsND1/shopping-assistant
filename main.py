"""
Главное меню приложения "Умный список покупок"
Объединяет все модули:
- categories.py - управление категориями
- products.py - управление товарами
- lists.py - управление списками покупок
- purchases.py - статистика и аналитика
"""

import os
import sys
from datetime import datetime

# Импортируем все модули
import db
import categories as cat
import products as prod
import lists
import purchases


# ============================================
# НАСТРОЙКИ
# ============================================

DATA_BASE = "data_products.db"
VERSION = "1.0.0"


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def clear_screen():
    """Очищает экран консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title):
    """Печатает красивый заголовок"""
    print("\n" + "=" * 70)
    print(f" 🛒 УМНЫЙ СПИСОК ПОКУПОК v{VERSION} — {title}")
    print("=" * 70)


def print_menu(options):
    """Печатает меню с вариантами"""
    print("\n" + "-" * 40)
    for key, value in options.items():
        print(f" {key}. {value}")
    print("-" * 40)


def wait_for_user():
    """Ждёт нажатия Enter"""
    input("\n Нажмите Enter, чтобы продолжить...")


def check_database():
    """Проверяет, создана ли база данных"""
    import sqlite3
    try:
        with db.get_connection(DATA_BASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
            if not cursor.fetchone():
                print(" База данных не инициализирована. Создаём таблицы...")
                db.init_database()
                return False
            return True
    except:
        print(" Ошибка подключения к базе данных")
        return False


# ============================================
# МЕНЮ КАТЕГОРИЙ
# ============================================

def menu_categories():
    """Меню управления категориями"""
    while True:
        clear_screen()
        print_header("УПРАВЛЕНИЕ КАТЕГОРИЯМИ")
        
        print_menu({
            "1": "Показать все категории",
            "2": "Добавить категорию",
            "3": "Найти категорию по ID",
            "4": "Изменить категорию",
            "5": "Удалить категорию",
            "0": "Вернуться в главное меню"
        })
        
        choice = input(" Выберите действие: ").strip()
        
        if choice == "1":
            cat.get_all_categories(DATA_BASE)
            wait_for_user()
        
        elif choice == "2":
            name = input(" Введите название категории: ").strip()
            if name:
                desc = input(" Введите описание (можно пропустить): ").strip()
                cat.create_category(name, desc if desc else None, DATA_BASE)
            else:
                print(" Название не может быть пустым")
            wait_for_user()
        
        elif choice == "3":
            try:
                cat_id = int(input(" Введите ID категории: "))
                cat.get_category_by_id(DATA_BASE, cat_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "4":
            try:
                cat_id = int(input(" Введите ID категории для изменения: "))
                
                # Получаем текущие данные
                with db.get_connection(DATA_BASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, description FROM categories WHERE id = ?", (cat_id,))
                    current = cursor.fetchone()
                    
                    if not current:
                        print(f" Категория с ID={cat_id} не найдена")
                        wait_for_user()
                        continue
                
                print(f"\n Текущее название: {current[0]}")
                print(f" Текущее описание: {current[1] or 'нет'}")
                
                new_name = input("\n Новое название (Enter - оставить): ").strip()
                new_desc = input(" Новое описание (Enter - оставить): ").strip()
                
                cat.update_category(DATA_BASE, cat_id, 
                                   new_name if new_name else None,
                                   new_desc if new_desc else None)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "5":
            try:
                cat_id = int(input(" Введите ID категории для удаления: "))
                cat.delete_category_by_id(DATA_BASE, cat_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "0":
            break
        
        else:
            print(" Неверный выбор")
            wait_for_user()


# ============================================
# МЕНЮ ТОВАРОВ
# ============================================

def menu_products():
    """Меню управления товарами"""
    while True:
        clear_screen()
        print_header("УПРАВЛЕНИЕ ТОВАРАМИ")
        
        print_menu({
            "1": "Показать все товары",
            "2": "Добавить товар",
            "3": "Найти товар по названию",
            "4": "Найти товар по ID",
            "5": "Изменить товар",
            "6": "Удалить товар",
            "0": "Вернуться в главное меню"
        })
        
        choice = input(" Выберите действие: ").strip()
        
        if choice == "1":
            prod.list_all_products(DATA_BASE)
            wait_for_user()
        
        elif choice == "2":
            prod.create_product(DATA_BASE)
            wait_for_user()
        
        elif choice == "3":
            prod.get_product(DATA_BASE)
            wait_for_user()
        
        elif choice == "4":
            prod.get_product_by_id(DATA_BASE)
            wait_for_user()
        
        elif choice == "5":
            prod.update_product(DATA_BASE)
            wait_for_user()
        
        elif choice == "6":
            prod.delete_product(DATA_BASE)
            wait_for_user()
        
        elif choice == "0":
            break
        
        else:
            print(" Неверный выбор")
            wait_for_user()


# ============================================
# МЕНЮ СПИСКОВ
# ============================================

def menu_lists():
    """Меню управления списками покупок"""
    while True:
        clear_screen()
        print_header("СПИСКИ ПОКУПОК")
        
        print_menu({
            "1": "Показать все списки",
            "2": "Создать новый список",
            "3": "Показать содержимое списка",
            "4": "Добавить товар в список",
            "5": "Отметить товар как купленный",
            "6": "Отметить несколько товаров",
            "7": "Изменить количество товара",
            "8": "Удалить товар из списка",
            "9": "Завершить список",
            "10": "Удалить список",
            "11": "Поиск по спискам",
            "12": "Сводка по активным спискам",
            "0": "Вернуться в главное меню"
        })
        
        choice = input(" Выберите действие: ").strip()
        
        if choice == "1":
            show_all = input(" Показать завершённые? (да/нет): ").lower() == 'да'
            lists.get_all_lists(DATA_BASE, show_completed=show_all)
            wait_for_user()
        
        elif choice == "2":
            name = input(" Название списка (Enter - авто): ").strip()
            lists.create_shopping_list(DATA_BASE, name if name else None)
            wait_for_user()
        
        elif choice == "3":
            try:
                list_id = int(input(" Введите ID списка: "))
                lists.display_list(DATA_BASE, list_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "4":
            try:
                list_id = int(input(" Введите ID списка: "))
                qty = input(" Количество (по умолч. 1): ").strip()
                qty = float(qty) if qty else 1
                lists.add_item_to_list(DATA_BASE, list_id, quantity=qty)
            except ValueError:
                print(" Ошибка: неверный формат числа")
            wait_for_user()
        
        elif choice == "5":
            try:
                item_id = int(input(" Введите ID позиции: "))
                price = input(" Цена за единицу (Enter - стандартная): ").strip()
                lists.mark_item_as_bought(DATA_BASE, item_id, price if price else None)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "6":
            try:
                list_id = int(input(" Введите ID списка: "))
                lists.mark_multiple_items(DATA_BASE, list_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "7":
            try:
                item_id = int(input(" Введите ID позиции: "))
                qty = float(input(" Новое количество: "))
                lists.update_item_quantity(DATA_BASE, item_id, qty)
            except ValueError:
                print(" Ошибка: неверный формат числа")
            wait_for_user()
        
        elif choice == "8":
            try:
                item_id = int(input(" Введите ID позиции: "))
                lists.remove_item_from_list(DATA_BASE, item_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "9":
            try:
                list_id = int(input(" Введите ID списка: "))
                lists.complete_list(DATA_BASE, list_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "10":
            try:
                list_id = int(input(" Введите ID списка: "))
                confirm = input(f" Удалить список ID={list_id}? (да/нет): ")
                if confirm.lower() == 'да':
                    lists.delete_list(DATA_BASE, list_id)
            except ValueError:
                print(" Ошибка: ID должен быть числом")
            wait_for_user()
        
        elif choice == "11":
            term = input(" Введите текст для поиска: ").strip()
            if term:
                lists.search_in_lists(DATA_BASE, term)
            else:
                print(" Введите текст для поиска")
            wait_for_user()
        
        elif choice == "12":
            lists.get_active_lists_summary(DATA_BASE)
            wait_for_user()
        
        elif choice == "0":
            break
        
        else:
            print(" Неверный выбор")
            wait_for_user()


# ============================================
# МЕНЮ СТАТИСТИКИ
# ============================================

def menu_statistics():
    """Меню статистики и аналитики"""
    while True:
        clear_screen()
        print_header("СТАТИСТИКА И АНАЛИТИКА")
        
        print_menu({
            "1": "Сводка расходов",
            "2": "Расходы по категориям",
            "3": "Топ товаров",
            "4": "Статистика по дням",
            "5": "Сравнение по месяцам",
            "6": "Товары, которые давно не покупали",
            "7": "Тренды категорий",
            "8": "Полезные советы",
            "9": "Экспорт отчёта в файл",
            "0": "Вернуться в главное меню"
        })
        
        choice = input(" Выберите действие: ").strip()
        
        if choice == "1":
            print("\n Выберите период:")
            print(" 1. День")
            print(" 2. Неделя")
            print(" 3. Месяц")
            print(" 4. Год")
            print(" 5. Всё время")
            
            period_choice = input(" > ").strip()
            period_map = {'1': 'day', '2': 'week', '3': 'month', '4': 'year', '5': 'all'}
            period = period_map.get(period_choice, 'month')
            
            purchases.get_spending_summary(DATA_BASE, period)
            wait_for_user()
        
        elif choice == "2":
            print("\n Выберите период:")
            print(" 1. День")
            print(" 2. Неделя")
            print(" 3. Месяц")
            print(" 4. Год")
            print(" 5. Всё время")
            
            period_choice = input(" > ").strip()
            period_map = {'1': 'day', '2': 'week', '3': 'month', '4': 'year', '5': 'all'}
            period = period_map.get(period_choice, 'month')
            
            purchases.get_spending_by_category(DATA_BASE, period)
            wait_for_user()
        
        elif choice == "3":
            purchases.get_top_products(DATA_BASE, 'all', 10)
            wait_for_user()
        
        elif choice == "4":
            try:
                days = int(input(" Сколько дней проанализировать? (по умолч. 30): ") or "30")
                purchases.get_daily_stats(DATA_BASE, days)
            except ValueError:
                print(" Ошибка: введите число")
            wait_for_user()
        
        elif choice == "5":
            purchases.get_monthly_comparison(DATA_BASE)
            wait_for_user()
        
        elif choice == "6":
            try:
                days = int(input(" Сколько дней без покупок считать? (по умолч. 30): ") or "30")
                purchases.get_unused_products(DATA_BASE, days)
            except ValueError:
                print(" Ошибка: введите число")
            wait_for_user()
        
        elif choice == "7":
            purchases.get_category_trends(DATA_BASE)
            wait_for_user()
        
        elif choice == "8":
            purchases.get_shopping_tips(DATA_BASE)
            wait_for_user()
        
        elif choice == "9":
            filename = input(" Имя файла (по умолч. stats_report.txt): ").strip()
            if not filename:
                filename = "stats_report.txt"
            purchases.export_stats_to_text(DATA_BASE, filename)
            wait_for_user()
        
        elif choice == "0":
            break
        
        else:
            print(" Неверный выбор")
            wait_for_user()


# ============================================
# ИНФОРМАЦИЯ О ПРИЛОЖЕНИИ
# ============================================

def show_info():
    """Показывает информацию о приложении"""
    clear_screen()
    print_header("О ПРИЛОЖЕНИИ")
    
    print("""
    🛒 Умный список покупок v1.0.0
    
    Приложение для управления покупками:
    • Категории товаров
    • Товары и цены
    • Списки покупок
    • История и статистика
    
    Модули:
    • categories.py - управление категориями
    • products.py - управление товарами
    • lists.py - управление списками
    • purchases.py - статистика
    • db.py - работа с базой данных
    
    База данных: SQLite (data_products.db)
    
    Разработано в рамках обучения Python
    """)
    
    wait_for_user()


# ============================================
# ГЛАВНОЕ МЕНЮ
# ============================================

def main():
    """Главная функция приложения"""
    
    # Проверяем базу данных при запуске
    check_database()
    
    while True:
        clear_screen()
        print_header("ГЛАВНОЕ МЕНЮ")
        
        print_menu({
            "1": "📁 Управление категориями",
            "2": "📦 Управление товарами",
            "3": "📋 Управление списками покупок",
            "4": "📊 Статистика и аналитика",
            "5": "ℹ️ О программе",
            "0": "🚪 Выход"
        })
        
        choice = input(" Выберите раздел: ").strip()
        
        if choice == "1":
            menu_categories()
        
        elif choice == "2":
            menu_products()
        
        elif choice == "3":
            menu_lists()
        
        elif choice == "4":
            menu_statistics()
        
        elif choice == "5":
            show_info()
        
        elif choice == "0":
            clear_screen()
            print("\n" + "=" * 70)
            print(" Спасибо за использование приложения!")
            print(" До свидания!")
            print("=" * 70 + "\n")
            sys.exit(0)
        
        else:
            print(" Неверный выбор")
            wait_for_user()


# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\n Нажмите Enter для выхода...")