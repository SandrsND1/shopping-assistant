"""
Модуль для работы со списками покупок
Функции:
- Создание, просмотр, обновление и удаление списков
- Добавление товаров в список
- Отметка товаров как купленных
- Управление позициями в списке
"""

import sqlite3 as sq
from datetime import datetime
import db
import products as prod
import categories as cat


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def _get_list_status(list_data):
    """
    Определяет статус списка по данным из БД
    Возвращает: (статус_текст, активный_флаг)
    """
    if list_data is None:
        return "не найден", False
    
    # list_data ожидается в формате (id, name, created_at, completed_at)
    if len(list_data) >= 4 and list_data[3] is not None:
        return f"завершён ({list_data[3]})", False
    else:
        return "активен", True


def _format_datetime(dt_str):
    """Форматирует дату из БД в читаемый вид"""
    if not dt_str:
        return "не указана"
    try:
        # Обрезаем секунды и милисекунды для читаемости
        return dt_str[:16]  # YYYY-MM-DD HH:MM
    except:
        return str(dt_str)


def _get_category_name_by_id(data_base, category_id):
    """Получает название категории по ID (для внутреннего использования)"""
    if category_id is None:
        return "без категории"
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        result = cursor.fetchone()
        return result[0] if result else "категория удалена"


# ============================================
# ОСНОВНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ СО СПИСКАМИ
# ============================================

def create_shopping_list(data_base, name=None):
    """
    Создаёт новый список покупок
    
    Параметры:
        data_base: путь к файлу БД
        name: название списка (если None, генерируется автоматически)
    
    Возвращает:
        ID созданного списка или None при ошибке
    """
    # Генерируем название, если не указано
    if not name or name.strip() == "":
        from datetime import datetime
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        name = f"Список от {current_date}"
    else:
        name = name.strip()
        if len(name) > 100:
            print("Название слишком длинное (макс. 100 символов)")
            return None
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO shopping_lists (name, created_at)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (name,))
        
        list_id = cursor.lastrowid
        print(f"Создан новый список: '{name}' (ID={list_id})")
        return list_id


def get_all_lists(data_base, show_completed=True, limit=None):
    """
    Получает все списки покупок
    
    Параметры:
        data_base: путь к БД
        show_completed: показывать завершённые (True) или только активные (False)
        limit: ограничение количества записей
    
    Возвращает:
        Список кортежей (id, name, created_at, completed_at, items_count, bought_count)
    """
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Базовый запрос с подсчётом позиций
        query = '''
            SELECT 
                sl.id,
                sl.name,
                sl.created_at,
                sl.completed_at,
                COUNT(li.id) as total_items,
                SUM(CASE WHEN li.is_bought = 1 THEN 1 ELSE 0 END) as bought_items
            FROM shopping_lists sl
            LEFT JOIN list_items li ON sl.id = li.list_id
        '''
        
        # Добавляем фильтр по статусу
        if not show_completed:
            query += " WHERE sl.completed_at IS NULL"
        
        # Группировка и сортировка
        query += " GROUP BY sl.id ORDER BY sl.created_at DESC"
        
        # Ограничение
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        lists = cursor.fetchall()
        
        if not lists:
            print("Списки не найдены")
            return []
        
        # Выводим результат
        print("\n" + "=" * 70)
        print("СПИСКИ ПОКУПОК:")
        print("=" * 70)
        
        for lst in lists:
            list_id, name, created, completed, total, bought = lst
            status_text = "✅ ЗАВЕРШЁН" if completed else "🔄 АКТИВЕН"
            created_fmt = _format_datetime(created)
            
            print(f"\nID: {list_id} | {name}")
            print(f"  Статус: {status_text}")
            print(f"  Создан: {created_fmt}")
            if completed:
                print(f"  Завершён: {_format_datetime(completed)}")
            if total > 0:
                progress = (bought / total) * 100 if total > 0 else 0
                print(f"  Прогресс: {bought}/{total} ({progress:.1f}%)")
            else:
                print(f"  Прогресс: нет товаров")
        
        return lists


def get_list_by_id(data_base, list_id):
    """
    Получает информацию о списке по ID
    
    Возвращает словарь с данными списка или None
    """
    try:
        list_id = int(list_id)
    except (ValueError, TypeError):
        print("Ошибка: ID должен быть числом")
        return None
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Основная информация о списке
        cursor.execute('''
            SELECT id, name, created_at, completed_at
            FROM shopping_lists
            WHERE id = ?
        ''', (list_id,))
        
        list_data = cursor.fetchone()
        
        if not list_data:
            print(f"Список с ID={list_id} не найден")
            return None
        
        # Собираем данные в словарь
        result = {
            'id': list_data[0],
            'name': list_data[1],
            'created_at': list_data[2],
            'completed_at': list_data[3],
            'is_active': list_data[3] is None,
            'items': []
        }
        
        # Получаем все позиции в списке
        cursor.execute('''
            SELECT 
                li.id,
                li.product_id,
                p.name as product_name,
                c.name as category_name,
                li.quantity,
                li.is_bought,
                li.price_at_purchase,
                li.added_at
            FROM list_items li
            JOIN products p ON li.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE li.list_id = ?
            ORDER BY li.is_bought, li.added_at
        ''', (list_id,))
        
        items = cursor.fetchall()
        
        for item in items:
            result['items'].append({
                'item_id': item[0],
                'product_id': item[1],
                'product_name': item[2],
                'category': item[3] or 'без категории',
                'quantity': item[4],
                'is_bought': bool(item[5]),
                'price': item[6],
                'added_at': item[7]
            })
        
        return result


def display_list(data_base, list_id):
    """
    Красиво отображает содержимое списка
    """
    list_data = get_list_by_id(data_base, list_id)
    
    if not list_data:
        return
    
    print("\n" + "=" * 70)
    print(f"СПИСОК: {list_data['name']}")
    print("=" * 70)
    print(f"ID: {list_data['id']}")
    print(f"Создан: {_format_datetime(list_data['created_at'])}")
    
    if list_data['completed_at']:
        print(f"Завершён: {_format_datetime(list_data['completed_at'])}")
    else:
        print("Статус: АКТИВЕН")
    
    print("-" * 70)
    
    if not list_data['items']:
        print("В списке нет товаров")
        return
    
    # Группируем товары: сначала некупленные, потом купленные
    not_bought = [item for item in list_data['items'] if not item['is_bought']]
    bought = [item for item in list_data['items'] if item['is_bought']]
    
    total_sum = 0
    
    if not_bought:
        print("\n🛒 ОЖИДАЮТ ПОКУПКИ:")
        for idx, item in enumerate(not_bought, 1):
            print(f"  {idx}. [{item['item_id']}] {item['product_name']}")
            print(f"     Категория: {item['category']}")
            print(f"     Количество: {item['quantity']}")
            if item['price']:
                print(f"     Цена: {item['price']} руб")
    
    if bought:
        print("\n✅ УЖЕ КУПЛЕНО:")
        for idx, item in enumerate(bought, 1):
            price_info = f"по {item['price']} руб" if item['price'] else "цена не указана"
            item_sum = item['quantity'] * (item['price'] or 0)
            total_sum += item_sum
            print(f"  {idx}. {item['product_name']} — {item['quantity']} {price_info}")
            print(f"     Сумма: {item_sum:.2f} руб")
    
    if total_sum > 0:
        print("-" * 70)
        print(f"💰 ИТОГО ПОТРАЧЕНО: {total_sum:.2f} руб")
    
    print("=" * 70)


def complete_list(data_base, list_id):
    """
    Завершает список (проставляет completed_at)
    
    Возвращает True при успехе, False при ошибке
    """
    try:
        list_id = int(list_id)
    except ValueError:
        print("Ошибка: ID должен быть числом")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Проверяем существование и статус списка
        cursor.execute("SELECT name, completed_at FROM shopping_lists WHERE id = ?", (list_id,))
        list_data = cursor.fetchone()
        
        if not list_data:
            print(f"Список с ID={list_id} не найден")
            return False
        
        if list_data[1] is not None:
            print(f"Список '{list_data[0]}' уже завершён")
            return False
        
        # Проверяем некупленные позиции
        cursor.execute("SELECT COUNT(*) FROM list_items WHERE list_id = ? AND is_bought = 0", (list_id,))
        not_bought = cursor.fetchone()[0]
        
        if not_bought > 0:
            print(f"В списке {not_bought} некупленных позиций")
            response = input("Всё равно завершить список? (да/нет): ")
            if response.lower() != 'да':
                print("Завершение отменено")
                return False
        
        # Завершаем список
        cursor.execute('''
            UPDATE shopping_lists 
            SET completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (list_id,))
        
        print(f"Список '{list_data[0]}' (ID={list_id}) завершён")
        return True


def delete_list(data_base, list_id, delete_items=True):
    """
    Удаляет список и все связанные позиции
    
    Параметры:
        data_base: путь к БД
        list_id: ID списка
        delete_items: удалять ли связанные позиции (иначе только список)
    
    Возвращает True при успехе
    """
    try:
        list_id = int(list_id)
    except ValueError:
        print("Ошибка: ID должен быть числом")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Начинаем транзакцию
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Проверяем существование списка
            cursor.execute("SELECT name FROM shopping_lists WHERE id = ?", (list_id,))
            list_data = cursor.fetchone()
            
            if not list_data:
                print(f"Список с ID={list_id} не найден")
                cursor.execute("ROLLBACK")
                return False
            
            list_name = list_data[0]
            
            # Получаем информацию о позициях
            cursor.execute("SELECT COUNT(*) FROM list_items WHERE list_id = ?", (list_id,))
            items_count = cursor.fetchone()[0]
            
            if items_count > 0:
                print(f"В списке {items_count} позиций")
                
                if delete_items:
                    # Удаляем позиции
                    cursor.execute("DELETE FROM list_items WHERE list_id = ?", (list_id,))
                    print(f"Удалено позиций: {cursor.rowcount}")
                    
                    # Также удаляем из истории покупок (опционально)
                    cursor.execute("DELETE FROM purchase_history WHERE list_id = ?", (list_id,))
                    if cursor.rowcount > 0:
                        print(f"Удалено из истории: {cursor.rowcount}")
                else:
                    # Отвязываем позиции от списка (обнуляем list_id)
                    cursor.execute("UPDATE list_items SET list_id = NULL WHERE list_id = ?", (list_id,))
                    print("Позиции отвязаны от списка")
            
            # Удаляем сам список
            cursor.execute("DELETE FROM shopping_lists WHERE id = ?", (list_id,))
            
            cursor.execute("COMMIT")
            print(f"Список '{list_name}' (ID={list_id}) удалён")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Ошибка при удалении: {e}")
            return False


# ============================================
# РАБОТА С ПОЗИЦИЯМИ В СПИСКЕ
# ============================================

def add_item_to_list(data_base, list_id, product_id=None, quantity=1):
    """
    Добавляет товар в список покупок
    
    Параметры:
        data_base: путь к БД
        list_id: ID списка
        product_id: ID товара (если None, будет поиск)
        quantity: количество
    
    Возвращает ID созданной позиции или None
    """
    try:
        list_id = int(list_id)
    except ValueError:
        print("Ошибка: ID списка должен быть числом")
        return None
    
    # Проверяем количество
    try:
        quantity = float(quantity)
        if quantity <= 0:
            print("Количество должно быть положительным")
            return None
    except ValueError:
        print("Ошибка: количество должно быть числом")
        return None
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Проверяем, активен ли список
        cursor.execute("SELECT completed_at FROM shopping_lists WHERE id = ?", (list_id,))
        list_status = cursor.fetchone()
        
        if not list_status:
            print(f"Список с ID={list_id} не найден")
            return None
        
        if list_status[0] is not None:
            print("Нельзя добавлять товары в завершённый список")
            return None
        
        # Если product_id не указан, ищем товар
        if product_id is None:
            # Показываем товары для выбора
            print("\nДоступные товары:")
            
            # Получаем товары по категориям
            cursor.execute('''
                SELECT c.name, p.id, p.name, p.typical_price, p.unit
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY c.name, p.name
            ''')
            
            products = cursor.fetchall()
            
            if not products:
                print("Нет доступных товаров. Сначала создайте товары.")
                return None
            
            current_category = None
            for prod in products:
                category = prod[0] or "Без категории"
                if category != current_category:
                    print(f"\n{category}:")
                    current_category = category
                print(f"  ID:{prod[1]} | {prod[2]} | {prod[3]} руб/ед | {prod[4]}")
            
            # Запрашиваем ID товара
            try:
                product_id = int(input("\nВведите ID товара: "))
            except ValueError:
                print("Ошибка: ID должен быть числом")
                return None
            
            # Проверяем, существует ли товар
            cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
            if not cursor.fetchone():
                print(f"Товар с ID={product_id} не найден")
                return None
        
        # Проверяем, нет ли уже такого товара в списке
        cursor.execute('''
            SELECT id, quantity FROM list_items 
            WHERE list_id = ? AND product_id = ? AND is_bought = 0
        ''', (list_id, product_id))
        
        existing = cursor.fetchone()
        
        if existing:
            print(f"Товар уже есть в списке (ID позиции: {existing[0]})")
            response = input("Добавить к существующему количеству? (да/нет): ")
            if response.lower() == 'да':
                new_quantity = existing[1] + quantity
                cursor.execute('''
                    UPDATE list_items SET quantity = ? 
                    WHERE id = ?
                ''', (new_quantity, existing[0]))
                print(f"Количество обновлено: теперь {new_quantity}")
                return existing[0]
            else:
                print("Добавление отменено")
                return None
        
        # Добавляем новую позицию
        cursor.execute('''
            INSERT INTO list_items (list_id, product_id, quantity, added_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (list_id, product_id, quantity))
        
        item_id = cursor.lastrowid
        
        # Получаем название товара для красивого вывода
        cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        product_name = cursor.fetchone()[0]
        
        print(f"Товар '{product_name}' (x{quantity}) добавлен в список ID={list_id}")
        return item_id


def mark_item_as_bought(data_base, item_id, price=None):
    """
    Отмечает позицию в списке как купленную
    
    Параметры:
        data_base: путь к БД
        item_id: ID позиции в list_items
        price: фактическая цена (если None, будет использована typical_price)
    
    Возвращает True при успехе
    """
    try:
        item_id = int(item_id)
    except ValueError:
        print("Ошибка: ID позиции должен быть числом")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Начинаем транзакцию
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Получаем информацию о позиции
            cursor.execute('''
                SELECT li.list_id, li.product_id, li.quantity, li.is_bought,
                       sl.completed_at, p.name, p.typical_price
                FROM list_items li
                JOIN shopping_lists sl ON li.list_id = sl.id
                JOIN products p ON li.product_id = p.id
                WHERE li.id = ?
            ''', (item_id,))
            
            item = cursor.fetchone()
            
            if not item:
                print(f"Позиция с ID={item_id} не найдена")
                cursor.execute("ROLLBACK")
                return False
            
            list_id, product_id, quantity, is_bought, list_completed, product_name, default_price = item
            
            if is_bought:
                print("Эта позиция уже отмечена как купленная")
                cursor.execute("ROLLBACK")
                return False
            
            if list_completed:
                print("Нельзя отмечать покупки в завершённом списке")
                cursor.execute("ROLLBACK")
                return False
            
            # Определяем цену
            if price is None:
                price = default_price
                print(f"Цена не указана, используется стандартная: {price} руб")
            else:
                try:
                    price = float(price)
                    if price < 0:
                        print("Цена не может быть отрицательной")
                        cursor.execute("ROLLBACK")
                        return False
                except ValueError:
                    print("Ошибка: цена должна быть числом")
                    cursor.execute("ROLLBACK")
                    return False
            
            # Обновляем позицию в списке
            cursor.execute('''
                UPDATE list_items 
                SET is_bought = 1, price_at_purchase = ?
                WHERE id = ?
            ''', (price, item_id))
            
            # Добавляем запись в историю покупок
            total = quantity * price
            cursor.execute('''
                INSERT INTO purchase_history 
                (product_id, list_id, quantity, price, total, purchased_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (product_id, list_id, quantity, price, total))
            
            cursor.execute("COMMIT")
            print(f"✅ {product_name} (x{quantity}) куплен(о) по цене {price} руб")
            print(f"   Сумма: {total:.2f} руб")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Ошибка при отметке покупки: {e}")
            return False


def mark_multiple_items(data_base, list_id):
    """
    Отмечает несколько товаров в списке как купленные
    """
    try:
        list_id = int(list_id)
    except ValueError:
        print("Ошибка: ID списка должен быть числом")
        return
    
    # Получаем текущий список
    list_data = get_list_by_id(data_base, list_id)
    
    if not list_data:
        return
    
    if list_data['completed_at']:
        print("Нельзя отмечать покупки в завершённом списке")
        return
    
    # Показываем только некупленные товары
    not_bought = [item for item in list_data['items'] if not item['is_bought']]
    
    if not not_bought:
        print("В списке нет некупленных товаров")
        return
    
    print("\nНЕКУПЛЕННЫЕ ТОВАРЫ:")
    for idx, item in enumerate(not_bought, 1):
        print(f"{idx}. {item['product_name']} — {item['quantity']}")
    
    print("\nВведите номера товаров через пробел (например: 1 3 5)")
    print("Или 'all' для отметки всего")
    
    choice = input("> ").strip()
    
    if choice.lower() == 'all':
        selected = not_bought
    else:
        try:
            indices = [int(x) - 1 for x in choice.split()]
            selected = [not_bought[i] for i in indices if 0 <= i < len(not_bought)]
        except (ValueError, IndexError):
            print("Неверный ввод")
            return
    
    if not selected:
        print("Нет выбранных товаров")
        return
    
    print(f"\nВыбрано товаров: {len(selected)}")
    
    # Для каждого товара запрашиваем цену
    for item in selected:
        print(f"\nТовар: {item['product_name']} (x{item['quantity']})")
        price_input = input("Цена за единицу (Enter для стандартной): ").strip()
        
        if price_input:
            try:
                price = float(price_input)
            except ValueError:
                print("Неверный формат, используется стандартная цена")
                price = None
        else:
            price = None
        
        mark_item_as_bought(data_base, item['item_id'], price)


def remove_item_from_list(data_base, item_id):
    """
    Удаляет позицию из списка
    """
    try:
        item_id = int(item_id)
    except ValueError:
        print("Ошибка: ID позиции должен быть числом")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Проверяем существование позиции и получаем информацию
        cursor.execute('''
            SELECT li.product_id, p.name, li.is_bought
            FROM list_items li
            JOIN products p ON li.product_id = p.id
            WHERE li.id = ?
        ''', (item_id,))
        
        item = cursor.fetchone()
        
        if not item:
            print(f"Позиция с ID={item_id} не найдена")
            return False
        
        product_name = item[1]
        is_bought = item[2]
        
        if is_bought:
            print(f"Товар '{product_name}' уже куплен. Удалить из истории?")
            response = input("Всё равно удалить? (да/нет): ")
            if response.lower() != 'да':
                print("Удаление отменено")
                return False
        
        # Удаляем позицию
        cursor.execute("DELETE FROM list_items WHERE id = ?", (item_id,))
        print(f"Позиция '{product_name}' удалена из списка")
        return True


def update_item_quantity(data_base, item_id, new_quantity):
    """
    Обновляет количество товара в списке
    """
    try:
        item_id = int(item_id)
        new_quantity = float(new_quantity)
        if new_quantity <= 0:
            print("Количество должно быть положительным")
            return False
    except ValueError:
        print("Ошибка: ID и количество должны быть числами")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        # Проверяем позицию
        cursor.execute('''
            SELECT p.name, li.is_bought
            FROM list_items li
            JOIN products p ON li.product_id = p.id
            WHERE li.id = ?
        ''', (item_id,))
        
        item = cursor.fetchone()
        
        if not item:
            print(f"Позиция с ID={item_id} не найдена")
            return False
        
        if item[1]:
            print("Нельзя изменить количество уже купленного товара")
            return False
        
        # Обновляем количество
        cursor.execute('''
            UPDATE list_items SET quantity = ?
            WHERE id = ?
        ''', (new_quantity, item_id))
        
        print(f"Количество товара '{item[0]}' изменено на {new_quantity}")
        return True


# ============================================
# ПОИСК И ФИЛЬТРАЦИЯ
# ============================================

def search_in_lists(data_base, search_term):
    """
    Ищет товары во всех списках по названию
    """
    if not search_term or search_term.strip() == "":
        print("Введите текст для поиска")
        return
    
    search_term = f"%{search_term.strip()}%"
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                sl.id as list_id,
                sl.name as list_name,
                sl.completed_at,
                p.id as product_id,
                p.name as product_name,
                li.quantity,
                li.is_bought,
                li.price_at_purchase
            FROM list_items li
            JOIN shopping_lists sl ON li.list_id = sl.id
            JOIN products p ON li.product_id = p.id
            WHERE p.name LIKE ?
            ORDER BY sl.created_at DESC, li.added_at DESC
        ''', (search_term,))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"Ничего не найдено по запросу '{search_term}'")
            return
        
        print(f"\nНайдено {len(results)} совпадений:")
        print("=" * 70)
        
        current_list = None
        for res in results:
            if res[0] != current_list:
                current_list = res[0]
                status = "✅ ЗАВЕРШЁН" if res[2] else "🔄 АКТИВЕН"
                print(f"\n📋 {res[1]} (ID:{res[0]}) - {status}")
            
            bought_status = "✅" if res[6] else "🔄"
            price_info = f", цена: {res[7]}" if res[7] else ""
            print(f"  {bought_status} {res[4]} — {res[5]} шт{price_info}")


def get_active_lists_summary(data_base):
    """
    Показывает сводку по активным спискам
    """
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                sl.id,
                sl.name,
                COUNT(li.id) as total,
                SUM(CASE WHEN li.is_bought = 1 THEN 1 ELSE 0 END) as bought,
                SUM(li.quantity * li.price_at_purchase) as total_spent
            FROM shopping_lists sl
            LEFT JOIN list_items li ON sl.id = li.list_id
            WHERE sl.completed_at IS NULL
            GROUP BY sl.id
            ORDER BY sl.created_at DESC
        ''')
        
        lists = cursor.fetchall()
        
        if not lists:
            print("Нет активных списков")
            return
        
        print("\n" + "=" * 60)
        print("АКТИВНЫЕ СПИСКИ - СВОДКА")
        print("=" * 60)
        
        grand_total = 0
        for lst in lists:
            list_id, name, total, bought, spent = lst
            progress = (bought / total * 100) if total > 0 else 0
            spent = spent or 0
            grand_total += spent
            
            print(f"\n📋 {name} (ID:{list_id})")
            print(f"   Прогресс: {bought}/{total} ({progress:.1f}%)")
            if spent > 0:
                print(f"   Потрачено: {spent:.2f} руб")
        
        if grand_total > 0:
            print("-" * 60)
            print(f"💰 ВСЕГО ПОТРАЧЕНО: {grand_total:.2f} руб")
        print("=" * 60)


# ============================================
# ТЕСТОВАЯ ФУНКЦИЯ
# ============================================

def test_module():
    """
    Интерактивное тестирование модуля lists.py
    """
    data_b = "data_products.db"
    
    while True:
        print("\n" + "=" * 50)
        print("МОДУЛЬ УПРАВЛЕНИЯ СПИСКАМИ ПОКУПОК")
        print("=" * 50)
        print("1. Создать новый список")
        print("2. Показать все списки")
        print("3. Показать содержимое списка")
        print("4. Добавить товар в список")
        print("5. Отметить товар как купленный")
        print("6. Отметить несколько товаров")
        print("7. Изменить количество товара")
        print("8. Удалить товар из списка")
        print("9. Завершить список")
        print("10. Удалить список")
        print("11. Поиск по спискам")
        print("12. Сводка по активным спискам")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == "1":
            name = input("Название списка (Enter для авто): ").strip()
            create_shopping_list(data_b, name if name else None)
        
        elif choice == "2":
            show_all = input("Показать завершённые? (да/нет): ").lower() == 'да'
            get_all_lists(data_b, show_completed=show_all)
        
        elif choice == "3":
            try:
                list_id = int(input("Введите ID списка: "))
                display_list(data_b, list_id)
            except ValueError:
                print("Ошибка: ID должен быть числом")
        
        elif choice == "4":
            try:
                list_id = int(input("Введите ID списка: "))
                quantity = float(input("Количество (по умолч. 1): ") or "1")
                add_item_to_list(data_b, list_id, quantity=quantity)
            except ValueError:
                print("Ошибка: неверный формат числа")
        
        elif choice == "5":
            try:
                item_id = int(input("Введите ID позиции: "))
                price = input("Цена за единицу (Enter для стандартной): ").strip()
                mark_item_as_bought(data_b, item_id, price if price else None)
            except ValueError:
                print("Ошибка: ID должен быть числом")
        
        elif choice == "6":
            try:
                list_id = int(input("Введите ID списка: "))
                mark_multiple_items(data_b, list_id)
            except ValueError:
                print("Ошибка: ID должен быть числом")
        
        elif choice == "7":
            try:
                item_id = int(input("Введите ID позиции: "))
                quantity = float(input("Новое количество: "))
                update_item_quantity(data_b, item_id, quantity)
            except ValueError:
                print("Ошибка: неверный формат числа")
        
        elif choice == "8":
            try:
                item_id = int(input("Введите ID позиции: "))
                remove_item_from_list(data_b, item_id)
            except ValueError:
                print("Ошибка: ID должен быть числом")
        
        elif choice == "9":
            try:
                list_id = int(input("Введите ID списка: "))
                complete_list(data_b, list_id)
            except ValueError:
                print("Ошибка: ID должен быть числом")
        
        elif choice == "10":
            try:
                list_id = int(input("Введите ID списка: "))
                confirm = input(f"Удалить список ID={list_id}? (да/нет): ")
                if confirm.lower() == 'да':
                    delete_list(data_b, list_id)
            except ValueError:
                print("Ошибка: ID должен быть числом")
        
        elif choice == "11":
            term = input("Введите текст для поиска: ")
            search_in_lists(data_b, term)
        
        elif choice == "12":
            get_active_lists_summary(data_b)
        
        elif choice == "0":
            print("Выход из модуля")
            break
        
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    test_module()