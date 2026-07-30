from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Ingredient:
    name: str              # Название, например: "Молоко"
    amount: float          # Количество, например: 0.5
    unit: str              # Ед. изм.: "л", "г", "шт"
    category: str = "Прочее"  # Отдел в магазине: "Молочка", "Овощи/Фрукты", "Бакалея"

@dataclass
class Recipe:
    id: str
    title: str
    category: str          # "Завтрак", "Мясо", "Десерты" и т.д.
    cooking_time: int      # В минутах
    ingredients: List[Ingredient]
    instructions: str
    image_path: Optional[str] = None  # Путь к фото

@dataclass
class Cart:
    recipes: List[Recipe] = field(default_factory=list)

    from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Ingredient:
    name: str
    amount: float
    unit: str
    category: str = "Прочее"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "amount": self.amount,
            "unit": self.unit,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ingredient":
        return cls(
            name=data.get("name", ""),
            amount=float(data.get("amount", 0)),
            unit=data.get("unit", ""),
            category=data.get("category", "Прочее")
        )

@dataclass
class Recipe:
    id: str
    title: str
    category: str
    cooking_time: int
    ingredients: List[Ingredient]
    instructions: str
    image_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "cooking_time": self.cooking_time,
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "instructions": self.instructions,
            "image_path": self.image_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            category=data.get("category", "Прочее"),
            cooking_time=int(data.get("cooking_time", 0)),
            ingredients=[Ingredient.from_dict(ing) for ing in data.get("ingredients", [])],
            instructions=data.get("instructions", ""),
            image_path=data.get("image_path")
        )