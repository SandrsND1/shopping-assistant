import sqlite3 as sq
from contextlib import contextmanager
import db
data_b = "data_products.db"
def create_category(name, discription, data_base):
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories")
        cat_names = cursor.fetchall()
        category_exist = False
        for i in cat_names[0]:
            if name == i:
                print("Такая категория есть!!!")
                category_exist = True
                break
        
        if not category_exist:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUE (?,?)", (name, discription)
            )
            print("Категория создана")
            return True
        else:
            print("Категория не создана")
            return False

def get_all_categories(data_base):
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        all_cat = cursor.fetchall()
        for i in all_cat:
            print(f"{i[0]}.Название категорий {i[1]}:\n  Описание {i[2]}")

def get_lens_cat(data_base):
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(id) FROM categories")
        count = cursor.fetchone()
        return count[0]
print(get_lens_cat(data_b))
def get_id_category(data_base, id):
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories where id = ?", (id,))
        a = cursor.fetchone()
        if a:
            print(f"Категория по ID {id} это {a[1]}")
        else:
            print(f"По ID = {id} нету категорий!")
        
def set_id_category(data_base, id, new_name= None, new_description= None):
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM categories WHERE id = ?",(id,))
        a = cursor.fetchone()
        if not a:
            print(f"По ID = {id} нету категорий!")
            return False
        name = new_name if new_name else a[0]
        description = description if description else a[1]

        cursor.execute("""
                    UPDATE categories
                       SET name = ?, description = ?
                       WHERE = ?
                       """, (name,description, id))
        print(f"ID={id} был обновлен на название {name} и описание {description}")
        return True
    
def delete_category_by_id(data_base, category_id):
    with db.get_connection(data_base) as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. Проверяем существование категории
            cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
            category = cursor.fetchone()
            
            if not category:
                print(f" Категория с ID = {category_id} не найдена")
                cursor.execute("ROLLBACK")
                return False
            
            category_name = category[0]
            print(f"Категория: {category_name}")
            
            # 2. Проверяем товары в категории
            cursor.execute("SELECT id, name FROM products WHERE category_id = ?", (category_id,))
            products = cursor.fetchall()
            
            if products:
                print(f"\nТовары в этой категории ({len(products)} шт.):")
                for i, (prod_id, prod_name) in enumerate(products, 1):
                    print(f"   {i}. {prod_name}")
                prod_delete = input(f"\nВсего {len(products)} товаров будет удалено. Удалить? (да/нет): ")
                
                if prod_delete.lower() == 'да':
                    cursor.execute("DELETE FROM products WHERE category_id = ?", (category_id,))
                    print(f"Удалено товаров: {len(products)}")
                else:
                    print("Удаление отменено")
                    cursor.execute("ROLLBACK")
                    return False
            else:
                print("В категории нет товаров")
            
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            
            cursor.execute("COMMIT")
            print(f"Категория '{category_name}' (ID={category_id}) успешно удалена")
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Ошибка при удалении: {e}")
            return False