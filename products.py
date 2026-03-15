import sqlite3 as sq
import db
import categories as cat

def create_product(data_base):

    name = input("Введите название продукта: ").strip()
    if not name:
        print("Название не может быть пустым!")
        return False

    try:
        price = float(input("Введите цену продукта: "))
        if price <= 0:
            print("Цена должна быть положительной!")
            return False
    except ValueError:
        print("Ошибка: введите число!")
        return False

    unit = input("Введите единицу измерения (шт/кг/л): ").strip().lower()
    valid_units = ['шт', 'кг', 'л', 'г', 'мл', 'упак']
    if unit not in valid_units:
        print(f"Допустимые единицы: {', '.join(valid_units)}")
        return False

    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY id")
        categories = cursor.fetchall()
        
        if not categories:
            print("Сначала создайте хотя бы одну категорию!")
            return False
        
        print("\nДоступные категории:")
        for cat_id, cat_name in categories:
            print(f"  {cat_id}. {cat_name}")
        
 
        try:
            id_cat = int(input("\nВведите ID категории: "))
            # Проверяем, что такой ID существует
            valid_ids = [c[0] for c in categories]
            if id_cat not in valid_ids:
                print("Категории с таким ID не существует!")
                return False
        except ValueError:
            print("Ошибка: ID должен быть числом!")
            return False
        

        cursor.execute("SELECT 1 FROM products WHERE name = ? AND category_id = ?", 
                      (name, id_cat))
        if cursor.fetchone():
            print("Такой продукт уже есть в этой категории!")
            return False
        

        cursor.execute('''
            INSERT INTO products (name, category_id, typical_price, unit, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, id_cat, price, unit))
        
        print(f"✅ Продукт '{name}' создан в категории ID={id_cat}")
        return True

def get_product(data_base):

    name = input("Введите название продукта (можно часть названия): ").strip()
    
    if not name:
        print("Название не может быть пустым!")
        return
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, c.name as category, p.typical_price, p.unit
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.name LIKE ?
            ORDER BY p.name
        ''', (f'%{name}%',))
        
        products = cursor.fetchall()
        
        if not products:
            print(f"Продукты, содержащие '{name}', не найдены")
            return
        
        print(f"\nНайдено продуктов: {len(products)}")
        print("-" * 60)
        for prod in products:
            print(f"ID:{prod[0]} | {prod[1]}")
            print(f"   Категория: {prod[2] or 'без категории'}")
            print(f"   Цена: {prod[3]} руб/ед")
            print(f"   Единица: {prod[4]}")
            print("-" * 40)

def get_product_by_id(data_base):

    try:
        prod_id = int(input("Введите ID продукта: "))
    except ValueError:
        print("Ошибка: ID должен быть числом!")
        return
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, c.name as category, p.typical_price, p.unit,
                   p.created_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        ''', (prod_id,))
        
        product = cursor.fetchone()
        
        if not product:
            print(f"Продукт с ID={prod_id} не найден")
            return
        
        print(f"\nИнформация о продукте ID={prod_id}:")
        print(f"  Название: {product[1]}")
        print(f"  Категория: {product[2] or 'не указана'}")
        print(f"  Цена: {product[3]} руб")
        print(f"  Единица: {product[4]}")
        print(f"  Дата создания: {product[5]}")
        
        # Показываем статистику покупок
        cursor.execute('''
            SELECT COUNT(*), SUM(quantity), AVG(price)
            FROM purchase_history
            WHERE product_id = ?
        ''', (prod_id,))
        
        stats = cursor.fetchone()
        if stats[0] > 0:
            print(f"\nСтатистика покупок:")
            print(f"  Куплено раз: {stats[0]}")
            print(f"  Всего единиц: {stats[1]:.1f}")
            print(f"  Средняя цена: {stats[2]:.2f} руб")

def update_product(data_base):
    try:
        product_id = int(input("Введите ID продукта для обновления: "))
    except ValueError:
        print("Ошибка: ID должен быть числом!")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT name, typical_price, unit, category_id FROM products WHERE id = ?", 
                      (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print(f"Продукт с ID {product_id} не найден")
            return False

        current_name, current_price, current_unit, current_cat = product

        cursor.execute("SELECT id, name FROM categories ORDER BY id")
        categories = cursor.fetchall()
        
        print(f"\nТекущие данные продукта:")
        print(f"  Название: {current_name}")
        print(f"  Цена: {current_price} руб")
        print(f"  Единица: {current_unit}")
        
        cat_name = next((c[1] for c in categories if c[0] == current_cat), "не указана")
        print(f"  Категория: {cat_name} (ID: {current_cat})")
        
        print("\nВведите новые значения (Enter - оставить без изменений):")
        
 
        new_name = input(f"Новое название [{current_name}]: ").strip()
        
       
        new_price_input = input(f"Новая цена [{current_price}]: ").strip()
        
        
        new_unit = input(f"Новая единица [{current_unit}]: ").strip()
        
        
        print("\nДоступные категории:")
        for cat_id, cat_name in categories:
            print(f"  {cat_id}. {cat_name}")
        new_cat_input = input(f"ID новой категории [{current_cat}]: ").strip()
        
        
        updates = []
        values = []
        
        if new_name:
            updates.append("name = ?")
            values.append(new_name)
        
        if new_price_input:
            try:
                new_price = float(new_price_input)
                if new_price > 0:
                    updates.append("typical_price = ?")
                    values.append(new_price)
                else:
                    print(" Цена должна быть положительной, оставлена текущая")
            except ValueError:
                print(" Неверный формат цены, оставлена текущая")
        
        if new_unit:
            updates.append("unit = ?")
            values.append(new_unit)
        
        if new_cat_input:
            try:
                new_cat = int(new_cat_input)
                # Проверяем, существует ли категория
                if any(c[0] == new_cat for c in categories):
                    updates.append("category_id = ?")
                    values.append(new_cat)
                else:
                    print(" Категория не существует, оставлена текущая")
            except ValueError:
                print(" Неверный формат ID категории")
        
        if not updates:
            print("ℹ Нет изменений для сохранения")
            return False
        
        
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        
        print(" Продукт успешно обновлён!")
        
        
        cursor.execute('''
            SELECT p.id, p.name, c.name, p.typical_price, p.unit
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        ''', (product_id,))
        updated = cursor.fetchone()
        
        print(f"\nНовые данные:")
        print(f"  ID: {updated[0]}")
        print(f"  Название: {updated[1]}")
        print(f"  Категория: {updated[2] or 'не указана'}")
        print(f"  Цена: {updated[3]} руб")
        print(f"  Единица: {updated[4]}")
        
        return True

def delete_product(data_base):
    """Удаление продукта с транзакцией"""
    try:
        prod_id = int(input("Введите ID продукта для удаления: "))
    except ValueError:
        print("Ошибка: ID должен быть числом!")
        return False
    
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
       
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            
            cursor.execute("SELECT name FROM products WHERE id = ?", (prod_id,))
            product = cursor.fetchone()
            
            if not product:
                print(f"Продукт с ID={prod_id} не найден")
                cursor.execute("ROLLBACK")
                return False
            
            product_name = product[0]
            print(f"\n Удаление продукта: '{product_name}' (ID={prod_id})")
            
            
            cursor.execute("SELECT COUNT(*) FROM list_items WHERE product_id = ?", (prod_id,))
            in_lists = cursor.fetchone()[0]
            
            if in_lists > 0:
                print(f"  Внимание: продукт есть в {in_lists} списках покупок!")
                
            
                cursor.execute("""
                    SELECT COUNT(*) FROM list_items 
                    WHERE product_id = ? AND is_bought = 0
                """, (prod_id,))
                not_bought = cursor.fetchone()[0]
                
                if not_bought > 0:
                    print(f"  Из них {not_bought} ещё не куплены!")
                
                response = input("Всё равно удалить продукт? (да/нет): ")
                if response.lower() != 'да':
                    print(" Удаление отменено")
                    cursor.execute("ROLLBACK")
                    return False
                
                
                cursor.execute("DELETE FROM list_items WHERE product_id = ?", (prod_id,))
                print(f" Удалено связей из списков: {cursor.rowcount}")
            
            
            cursor.execute("SELECT COUNT(*) FROM purchase_history WHERE product_id = ?", (prod_id,))
            in_history = cursor.fetchone()[0]
            
            if in_history > 0:
                print(f" Продукт есть в истории покупок ({in_history} записей)")
                response = input("Удалить и из истории? (да/нет): ")
                if response.lower() == 'да':
                    cursor.execute("DELETE FROM purchase_history WHERE product_id = ?", (prod_id,))
                    print(f" Удалено из истории: {cursor.rowcount}")
            
            
            cursor.execute("DELETE FROM products WHERE id = ?", (prod_id,))
            
            
            cursor.execute("COMMIT")
            print(f" Продукт '{product_name}' (ID={prod_id}) полностью удалён")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f" Ошибка при удалении: {e}")
            return False

def list_all_products(data_base):
    """Показать все продукты с группировкой по категориям"""
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, COUNT(p.id) as prod_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY c.name
        ''')
        
        categories = cursor.fetchall()
        
        if not categories:
            print("Нет категорий")
            return
        
        for cat in categories:
            print(f"\n {cat[1]} (категория ID:{cat[0]}) - товаров: {cat[2]}")
            
            if cat[2] > 0:
                cursor.execute('''
                    SELECT id, name, typical_price, unit
                    FROM products
                    WHERE category_id = ?
                    ORDER BY name
                ''', (cat[0],))
                
                products = cursor.fetchall()
                for prod in products:
                    print(f"   ├─ {prod[1]}")
                    print(f"   │  ID:{prod[0]} | {prod[2]} руб/ед | {prod[3]}")
        
        # Показываем товары без категории
        cursor.execute('''
            SELECT id, name, typical_price, unit
            FROM products
            WHERE category_id IS NULL
            ORDER BY name
        ''')
        
        orphan = cursor.fetchall()
        if orphan:
            print(f"\n Без категории - товаров: {len(orphan)}")
            for prod in orphan:
                print(f"   ├─ {prod[1]}")
                print(f"   │  ID:{prod[0]} | {prod[2]} руб/ед | {prod[3]}")

def test_module():
    """Тестирование всех функций модуля"""
    print("="*60)
    print("ТЕСТИРОВАНИЕ МОДУЛЯ PRODUCTS")
    print("="*60)
    
    data_b = "data_products.db"
    
    while True:
        print("\n" + "="*40)
        print("МЕНЮ ТЕСТИРОВАНИЯ")
        print("="*40)
        print("1. Создать продукт")
        print("2. Найти продукт по названию")
        print("3. Найти продукт по ID")
        print("4. Обновить продукт")
        print("5. Удалить продукт")
        print("6. Показать все продукты")
        print("0. Выход")
        
        choice = input("\n Выберите действие: ")
        
        if choice == "1":
            create_product(data_b)
        elif choice == "2":
            get_product(data_b)
        elif choice == "3":
            get_product_by_id(data_b)
        elif choice == "4":
            update_product(data_b)
        elif choice == "5":
            delete_product(data_b)
        elif choice == "6":
            list_all_products(data_b)
        elif choice == "0":
            print("Выход из тестирования")
            break
        else:
            print("Неверный выбор")

if __name__ == "__main__":
    test_module()