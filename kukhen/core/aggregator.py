from collections import defaultdict
from typing import List, Dict
from core.models import Recipe, Ingredient

class ShoppingListAggregator:
    @staticmethod
    def aggregate_ingredients(recipes: List[Recipe]) -> List[Ingredient]:
        """Складывает одинаковые ингредиенты из разных рецептов."""
        totals = {}  # Ключ: (название, ед_изм, отдел)

        for recipe in recipes:
            for ing in recipe.ingredients:
                key = (ing.name.lower().strip(), ing.unit.lower().strip(), ing.category)
                if key in totals:
                    totals[key] += ing.amount
                else:
                    totals[key] = ing.amount

        aggregated = []
        for (name, unit, category), amount in totals.items():
            aggregated.append(Ingredient(
                name=name.capitalize(),
                amount=amount,
                unit=unit,
                category=category
            ))
        return aggregated

    @staticmethod
    def group_by_store_department(ingredients: List[Ingredient]) -> Dict[str, List[Ingredient]]:
        """Группирует ингредиенты по отделам магазина (Молочка, Овощи и т.д.)."""
        grouped = defaultdict(list)
        for ing in ingredients:
            grouped[ing.category].append(ing)
        return dict(grouped)