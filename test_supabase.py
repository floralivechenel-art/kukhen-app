# test_supabase.py
from core.supabase_client import supabase

def test():
    try:
        # Пробуем записать тестовый рецепт
        data = {"id": "test_1", "data": {"title": "Тестовый блинчик"}}
        supabase.table("recipes").upsert(data).execute()
        print("✅ Запись успешно создана в Supabase!")

        # Пробуем прочитать обратно
        res = supabase.table("recipes").select("*").eq("id", "test_1").execute()
        print("✅ Прочитано из облака:", res.data)

        # Удаляем тест
        supabase.table("recipes").delete().eq("id", "test_1").execute()
        print("✅ Тест пройден, база откликнулась отлично!")
    except Exception as e:
        print("❌ Ошибка соединения:", e)

if __name__ == "__main__":
    test()
    