import json
import os
from typing import List, Optional
from core.models import Recipe

DEFAULT_CATEGORIES = ["Завтрак", "Мясо", "Рыба", "Гарниры", "Десерты", "Напитки"]

class RecipeRepository:
    def __init__(self, db_path: str = "database.json"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Проверяет существование файла базы. Если его нет — создает начальную структуру."""
        if not os.path.exists(self.db_path):
            initial_data = {
                "categories": DEFAULT_CATEGORIES,
                "recipes": []
            }
            self._save_data(initial_data)

    def _load_raw_data(self) -> dict:
        """Читает весь сырой JSON из файла."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"categories": DEFAULT_CATEGORIES, "recipes": []}

    def _save_data(self, data: dict):
        """Записывает словарь обратно в JSON."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- РАБОТА С КАТЕГОРИЯМИ ---

    def get_categories(self) -> List[str]:
        """Возвращает список всех категорий."""
        data = self._load_raw_data()
        return data.get("categories", DEFAULT_CATEGORIES)

    # --- РАБОТА С РЕЦЕПТАМИ ---

    def get_all_recipes(self) -> List[Recipe]:
        """Возвращает вообще все рецепты."""
        data = self._load_raw_data()
        return [Recipe.from_dict(item) for item in data.get("recipes", [])]

    def get_recipes_by_category(self, category_name: str) -> List[Recipe]:
        """Возвращает рецепты только из определенной категории."""
        all_recipes = self.get_all_recipes()
        return [r for r in all_recipes if r.category.lower() == category_name.lower()]

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Recipe]:
        """Находит один конкретный рецепт по его ID."""
        all_recipes = self.get_all_recipes()
        for recipe in all_recipes:
            if recipe.id == recipe_id:
                return recipe
        return None

    def add_recipe(self, recipe: Recipe):
        """Сохраняет рецепт в базу (создает новый или обновляет существующий)."""
        data = self._load_raw_data()
        recipes_list = data.get("recipes", [])
        recipe_dict = recipe.to_dict()
        
        updated = False
        for idx, existing_item in enumerate(recipes_list):
            if existing_item.get("id") == recipe.id:
                recipes_list[idx] = recipe_dict
                updated = True
                break
                
        if not updated:
            recipes_list.append(recipe_dict)
            
        data["recipes"] = recipes_list
        self._save_data(data)

    def delete_recipe(self, recipe_id: str):
        """Удаляет рецепт по ID."""
        data = self._load_raw_data()
        recipes_list = data.get("recipes", [])
        data["recipes"] = [r for r in recipes_list if r.get("id") != recipe_id]
        self._save_data(data)

    def get_known_ingredients(self) -> dict:
        """Собирает словарь известных ингредиентов: {название: (unit, category)}"""
        known = {}
        for recipe in self.get_all_recipes():
            for ing in recipe.ingredients:
                name_key = ing.name.strip().capitalize()
                if name_key and name_key not in known:
                    known[name_key] = {
                        "unit": ing.unit,
                        "category": ing.category
                    }
        return known

    # --- РАБОТА С КОРЗИНОЙ ---

    def get_cart_raw(self) -> dict:
        """Возвращает словарь корзины вида {'recipe_id': count}."""
        data = self._load_raw_data()
        cart = data.get("cart", {})
        # Предосторожность: если в базе остался старый формат (список), переделываем в словарь
        if isinstance(cart, list):
            cart = {r_id: 1 for r_id in cart}
        return cart

    def get_cart_recipes_with_counts(self) -> List[tuple[Recipe, int]]:
        """Возвращает список пар: (Объект Рецепта, Количество порций)."""
        cart_dict = self.get_cart_raw()
        all_recipes = self.get_all_recipes()
        
        result = []
        for recipe in all_recipes:
            if recipe.id in cart_dict:
                count = cart_dict[recipe.id]
                result.append((recipe, count))
        return result

    def add_to_cart(self, recipe_id: str, count: int = 1):
        """Добавляет рецепт в корзину или обновляет количество."""
        data = self._load_raw_data()
        cart = self.get_cart_raw()
        cart[recipe_id] = count
        data["cart"] = cart
        self._save_data(data)

    def remove_from_cart(self, recipe_id: str):
        """Удаляет рецепт из корзины."""
        data = self._load_raw_data()
        cart = self.get_cart_raw()
        if recipe_id in cart:
            del cart[recipe_id]
        data["cart"] = cart
        self._save_data(data)

    def get_recipe_cart_count(self, recipe_id: str) -> int:
        """Возвращает сколько порций блюда сейчас в корзине (0 если нет)."""
        cart = self.get_cart_raw()
        return cart.get(recipe_id, 0)
   


    # --- РАСЧЕТ ИНГРЕДИЕНТОВ ДЛЯ СПИСКА ПОКУПОК ---

    def calculate_shopping_list(self) -> dict:
        """
        Возвращает словарь агрегированных ингредиентов по отделам:
        {
            "Овощи/Фрукты": {
                ("Картофель", "кг"): 1.5,
                ...
            }, ...
        }
        """
        cart_items = self.get_cart_recipes_with_counts()
        aggregated = {}

        for recipe, portions in cart_items:
            for ing in recipe.ingredients:
                dept = ing.category or "Прочее"
                name_key = ing.name.strip().capitalize()
                unit = ing.unit
                total_amount = ing.amount * portions

                if dept not in aggregated:
                    aggregated[dept] = {}

                # Ключ — пара (Название, Единица измерения)
                item_key = (name_key, unit)
                if item_key in aggregated[dept]:
                    aggregated[dept][item_key] += total_amount
                else:
                    aggregated[dept][item_key] = total_amount

        return aggregated