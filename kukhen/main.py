import flet as ft
import uuid
from storage.repository import RecipeRepository
from core.models import Recipe, Ingredient
from google_drive import upload_backup_to_drive, download_backup_from_drive

UNITS = [
    "г", 
    "кг", 
    "мл", 
    "л", 
    "шт", 
    "ложка чайная", 
    "ложка столовая", 
    "упаковка", 
    "на глаз", 
    "щепотка", 
    "по вкусу"
]

DEPARTMENTS = [
    "Овощи/Фрукты", 
    "Молочные продукты", 
    "Мясо/Птица", 
    "Рыба/Морепродукты", 
    "Бакалея", 
    "Заморозка", 
    "Напитки", 
    "Соусы/Специи", 
    "Прочее"
]

def format_amount(val: float) -> str:
    """Форматирует число: 2.0 -> '2', а 0.5 -> '0.5'"""
    if val is None:
        return "0"
    if val.is_integer():
        return str(int(val))
    return str(round(val, 2))

def main(page: ft.Page):
    
    page.title = "KUKHEN — Личные рецепты"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 420
    page.window.height = 750
    page.padding = 15

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # Способ 1: Прямое создание объекта Padding (работает во всех версиях)
    page.padding = ft.Padding(left=15, top=12, right=15, bottom=24)

    repo = RecipeRepository()

    # 1. ОБЕРТКА ДЛЯ ОГРАНИЧЕНИЯ ШИРИНЫ (Ставим в самом верху!)
    def wrap_in_bounds(content_control):
        return ft.Row(
            [
                ft.Container(
                    content=content_control,
                    expand=True,
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    def handle_restore(e):
        snack = ft.SnackBar(ft.Text("Синхронизация рецептов с Google Диском..."))
        page.overlay.append(snack)
        snack.open = True
        page.update()

        success, message = download_backup_from_drive()
        
        if success:
            if hasattr(repo, "reload"):
                repo.reload()
            elif hasattr(repo, "load_data"):
                repo.load_data()

            show_main_view()

            success_snack = ft.SnackBar(ft.Text("Рецепты успешно восстановлены!"))
            page.overlay.append(success_snack)
            success_snack.open = True
        else:
            error_snack = ft.SnackBar(ft.Text(f"Ошибка: {message}"))
            page.overlay.append(error_snack)
            error_snack.open = True
            
        page.update()

    # Объявляем AppBar один раз
    main_appbar = ft.AppBar(
        title=ft.Text("Kukhen", weight=ft.FontWeight.BOLD),
        actions=[
            ft.IconButton(
                icon=ft.Icons.CLOUD_DOWNLOAD,
                tooltip="Восстановить из Google Диска",
                on_click=handle_restore,
            ),
        ],
        bgcolor=ft.Colors.ORANGE_50,
    )

    def auto_sync_to_drive():
        """Тихая отправка базы на Google Диск при изменениях"""
        try:
            # Отправляем копию в облако, не мешая пользователю
            upload_backup_to_drive()
        except Exception as err:
            print(f"Фоновая синхронизация пропущена: {err}")

    # Навигация между вкладками
    def on_nav_change(e):
        if e.control.selected_index == 0:
            show_main_view()
        elif e.control.selected_index == 1:
            show_cart_view()

    def get_nav_bar(current_index: int):
        return ft.NavigationBar(
            selected_index=current_index,
            on_change=on_nav_change,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.MENU_BOOK, label="Главная"),
                ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART, label="Корзина"),
            ]
        )

    def go_back_to_main(e=None):
        show_main_view()

    # --- 1. ФОРМА СОЗДАНИЯ / РЕДАКТИРОВАНИЯ РЕЦЕПТА ---

    def open_add_recipe_dialog(category_name: str, recipe_to_edit=None):
        known_ingredients = repo.get_known_ingredients()

        initial_title = recipe_to_edit.title if recipe_to_edit else ""
        initial_time = str(recipe_to_edit.cooking_time) if recipe_to_edit else "15"
        initial_comment = recipe_to_edit.comment if recipe_to_edit else ""

        title_input = ft.TextField(label="Название блюда", hint_text="Омлет с сыром", value=initial_title)
        time_input = ft.TextField(label="Время (мин)", keyboard_type=ft.KeyboardType.NUMBER, value=initial_time, width=120)
        comment_input = ft.TextField(label="Заметка к рецепту (необязательно)",hint_text="можно накормить табор",value=initial_comment, multiline=True, min_lines=1, max_lines=3)

        ingredients_column = ft.Column(spacing=10)
        steps_column = ft.Column(spacing=8)
    

        def add_ingredient_row(ing_data=None):
            def apply_known_pattern(e):
                entered_name = name_tf.value.strip().lower()
                for known_name, pattern in known_ingredients.items():
                    if known_name.lower() == entered_name:
                        unit_dd.value = pattern["unit"]
                        dept_dd.value = pattern["category"]
                        page.update()
                        break

            name_tf = ft.TextField(
                label="Название продукта",
                hint_text="например: Куриное филе",
                expand=True,
                value=ing_data.name if ing_data else "",
                on_change=apply_known_pattern,
                dense=True
            )

            amount_tf = ft.TextField(
                value=str(ing_data.amount) if ing_data else "1",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=100,
                label="Сколько",
                label_style=ft.TextStyle(size=10),
                text_size=15,
                dense=True
            )

            unit_dd = ft.Dropdown(
                width=110,
                options=[ft.dropdown.Option(u) for u in UNITS],
                value=ing_data.unit if ing_data else UNITS[0],
                label="Мерило",
                label_style=ft.TextStyle(size=10),
                text_size=15,
                dense=True
            )

            dept_dd = ft.Dropdown(
                expand=True,
                options=[ft.dropdown.Option(d) for d in DEPARTMENTS],
                value=ing_data.category if ing_data else DEPARTMENTS[0],
                label="Отдел магазина",
                label_style=ft.TextStyle(size=10),
                text_size=15,
                dense=True
            )

            def remove_row(card):
                ingredients_column.controls.remove(card)
                page.update()

            card_content = ft.Column(
                [
                    ft.Row(
                        [
                            name_tf,
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.RED_400,
                                on_click=lambda ev: remove_row(ing_card),
                                tooltip="Удалить ингредиент"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        [amount_tf, unit_dd],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=8,
                        wrap=True,
                        run_spacing=8,
                    ),
                    dept_dd
                ],
                spacing=8
            )

            ing_card = ft.Container(
                content=card_content,
                bgcolor=ft.Colors.GREY_100,
                border_radius=10,
                padding=12
            )

            ingredients_column.controls.append(ing_card)
            page.update()

        def add_step_row(step_text=""):
            step_num = len(steps_column.controls) + 1
            step_tf = ft.TextField(
                hint_text=f"Описание шага {step_num}", 
                value=step_text, 
                expand=True, 
                multiline=True, 
                min_lines=1
            )
            
            row = ft.Row(spacing=5)
            
            def remove_step(ev):
                steps_column.controls.remove(row)
                for idx, r in enumerate(steps_column.controls):
                    r.controls[0].hint_text = f"Описание шага {idx + 1}"
                page.update()

            delete_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=remove_step)
            
            row.controls = [step_tf, delete_btn]
            steps_column.controls.append(row)
            page.update()

        if recipe_to_edit:
            for ing in recipe_to_edit.ingredients:
                add_ingredient_row(ing_data=ing)
            
            lines = recipe_to_edit.instructions.split("\n")
            for line in lines:
                clean_line = line.split(". ", 1)[-1] if ". " in line else line
                if clean_line.strip():
                    add_step_row(step_text=clean_line)
        else:
            add_ingredient_row()
            add_step_row()

        def save_recipe(e):
            if not title_input.value or not title_input.value.strip():
                title_input.error_text = "Введите название!"
                page.update()
                return

            parsed_ingredients = []
            for card in ingredients_column.controls:
                # Безопасно достаем контролы из карточки
                col = getattr(card, "content", None)
                if not col or not getattr(col, "controls", None) or len(col.controls) < 2:
                    continue

                top_row = col.controls[0]
                bottom_row = col.controls[1]

                top_ctrls = getattr(top_row, "controls", [])
                bottom_ctrls = getattr(bottom_row, "controls", [])

                if not top_ctrls or len(bottom_ctrls) < 3:
                    continue

                name_field = top_ctrls[0]
                name_val = name_field.value.strip() if name_field.value else ""
        
                if name_val:
                    try:
                        amt_val = float(bottom_ctrls[0].value) if bottom_ctrls[0].value else 1.0
                    except ValueError:
                        amt_val = 1.0
            
                    unit_val = bottom_ctrls[1].value
                    dept_val = bottom_ctrls[2].value
            
                    parsed_ingredients.append(
                        Ingredient(name=name_val.capitalize(), amount=amt_val, unit=unit_val, category=dept_val)
                    )

            steps_text = []
            for idx, row in enumerate(steps_column.controls):
                row_ctrls = getattr(row, "controls", [])
                if row_ctrls and row_ctrls[0].value:
                    step_val = row_ctrls[0].value.strip()
                    if step_val:
                        steps_text.append(f"{idx + 1}. {step_val}")

            instructions = "\n".join(steps_text)
            recipe_id = recipe_to_edit.id if recipe_to_edit else str(uuid.uuid4())

            comment_val = comment_input.value.strip() if comment_input.value else ""

            updated_recipe = Recipe(
                id=recipe_id,
                title=title_input.value.strip(),
                category=category_name,
                cooking_time=int(time_input.value) if time_input.value and time_input.value.isdigit() else 15,
                ingredients=parsed_ingredients,
                instructions=instructions,
                comment=comment_val,
            )

            repo.add_recipe(updated_recipe)
            dialog.open = False
            page.update()
            show_category_view(category_name)

             # Автосинхронизация с Google Диском
            auto_sync_to_drive()


        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog_title = f"Редактировать: {recipe_to_edit.title}" if recipe_to_edit else f"Новый рецепт: {category_name}"

        dialog = ft.AlertDialog(
            title=ft.Text(dialog_title),
            content=ft.Container(
                content=ft.Column(
                    [
                        title_input,
                        time_input,
                        comment_input,
                        ft.Divider(),
                        ft.Text("Ингредиенты:", weight=ft.FontWeight.BOLD),
                        ingredients_column,
                        ft.TextButton("Ингредиент", icon=ft.Icons.ADD, on_click=lambda e: add_ingredient_row()),
                        ft.Divider(),
                        ft.Text("Шаги приготовления:", weight=ft.FontWeight.BOLD),
                        steps_column,
                        ft.TextButton("Шаг", icon=ft.Icons.ADD, on_click=lambda e: add_step_row()),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=380,
            ),
            actions=[
                ft.TextButton("Отмена", on_click=close_dialog),
                ft.ElevatedButton("Сохранить", on_click=save_recipe, style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_400, color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # --- 2. ПРОСМОТР РЕЦЕПТА И ВЫБОР ПОРЦИЙ ---

    def open_recipe_viewer(recipe):
        comment_widget = ft.Text(f"💡 {recipe.comment}", size=14, color=ft.Colors.GREY_700) if (hasattr(recipe, "comment") and recipe.comment and recipe.comment.strip()) else None
        ingredients_list = ft.Column(
            controls=[
                ft.Text(f"• {ing.name} — {format_amount(ing.amount)} {ing.unit}", size=14) 
                for ing in recipe.ingredients
            ],
            spacing=4
        )
        
        def close_viewer(e=None):
            viewer_dialog.open = False
            page.update()

        current_cart_count = repo.get_recipe_cart_count(recipe.id)
        portions_var = [current_cart_count if current_cart_count > 0 else 1]
        portions_label = ft.Text(str(portions_var[0]), size=16, weight=ft.FontWeight.BOLD)

        def change_portions(delta):
            new_val = portions_var[0] + delta
            if new_val >= 1:
                portions_var[0] = new_val
                portions_label.value = str(new_val)
                if repo.get_recipe_cart_count(recipe.id) > 0:
                    repo.add_to_cart(recipe.id, new_val)
                page.update()

        def toggle_cart_status(e):
            if repo.get_recipe_cart_count(recipe.id) > 0:
                repo.remove_from_cart(recipe.id)
            else:
                repo.add_to_cart(recipe.id, portions_var[0])
            close_viewer()
            show_category_view(recipe.category)

        is_in_cart = current_cart_count > 0
        cart_btn_text = "Убрать из корзины" if is_in_cart else "В корзину"
        cart_btn_color = ft.Colors.RED_400 if is_in_cart else ft.Colors.ORANGE_400

        def confirm_delete(e):
            def delete_and_close(ev):
                repo.delete_recipe(recipe.id)
                confirm_dialog.open = False
                viewer_dialog.open = False
                page.update()
                show_category_view(recipe.category)

            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Удалить рецепт?"),
                content=ft.Text(f"Вы точно хотите удалить '{recipe.title}'?"),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda ev: setattr(confirm_dialog, "open", False) or page.update()),
                    ft.ElevatedButton("Удалить", on_click=delete_and_close, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE)),
                ]
            )
            page.overlay.append(confirm_dialog)
            confirm_dialog.open = True
            page.update()
            
         # 🚀 Обновляем базу на Диске после удаления:
            auto_sync_to_drive()

        def edit_recipe(e):
            close_viewer()
            open_add_recipe_dialog(category_name=recipe.category, recipe_to_edit=recipe)

            # 🚀 Обновляем базу на Диске после удаления:
            auto_sync_to_drive()

        viewer_dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Text(recipe.title, weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE_600, on_click=edit_recipe),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=confirm_delete),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"⏱ Время: {recipe.cooking_time} мин.", color=ft.Colors.GREY_700),
                        ft.Divider(),
                        ft.Text("Ингредиенты (на 1 порцию):", weight=ft.FontWeight.BOLD, size=16),
                        ingredients_list,
                        ft.Divider(),
                        ft.Text("Как готовить:", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(recipe.instructions, size=14),
                        comment_widget if (hasattr(recipe, "comment") and recipe.comment and recipe.comment.strip()) else ft.Text("Заметок нет", color=ft.Colors.GREY_500),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Text("Порции:", weight=ft.FontWeight.BOLD),
                                ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=lambda e: change_portions(-1)),
                                portions_label,
                                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=lambda e: change_portions(1)),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=close_viewer),
                ft.ElevatedButton(
                    cart_btn_text, 
                    icon=ft.Icons.SHOPPING_CART, 
                    style=ft.ButtonStyle(bgcolor=cart_btn_color, color=ft.Colors.WHITE),
                    on_click=toggle_cart_status
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        page.overlay.append(viewer_dialog)
        viewer_dialog.open = True
        page.update()

    # --- 3. ЭКРАН КАТЕГОРИИ ---

    def show_category_view(category_name: str):
        page.controls.clear()
        page.appbar = main_appbar

        header = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=go_back_to_main,
                    tooltip="Назад",
                ),
                ft.Text(category_name, size=22, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        recipes = repo.get_recipes_by_category(category_name)

        def build_recipe_card(recipe: Recipe):
            in_cart = repo.get_recipe_cart_count(recipe.id) > 0

            def quick_toggle_cart(e):
                if in_cart:
                    repo.remove_from_cart(recipe.id)
                else:
                    repo.add_to_cart(recipe.id, 1)
                show_category_view(category_name)

            return ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.RESTAURANT,
                                        size=28,
                                        color=ft.Colors.ORANGE_700,
                                    ),
                                    ft.IconButton(
                                        icon=(
                                            ft.Icons.SHOPPING_CART
                                            if in_cart
                                            else ft.Icons.ADD_SHOPPING_CART
                                        ),
                                        icon_color=(
                                            ft.Colors.GREEN_600
                                            if in_cart
                                            else ft.Colors.GREY_400
                                        ),
                                        icon_size=20,
                                        tooltip=(
                                            "Убрать из корзины"
                                            if in_cart
                                            else "В корзину"
                                        ),
                                        on_click=quick_toggle_cart,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Text(
                                recipe.title,
                                weight=ft.FontWeight.BOLD,
                                size=14,
                                max_lines=1,
                                overflow="ellipsis",
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.ACCESS_TIME,
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Text(
                                        f"{recipe.cooking_time} мин",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    ink=True,
                    on_click=lambda e, r=recipe: open_recipe_viewer(r),
                )
            )

        add_card = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.ADD_CIRCLE_OUTLINE,
                        size=36,
                        color=ft.Colors.ORANGE_600,
                    ),
                    ft.Text(
                        "Добавить",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.ORANGE_50,
            border_radius=12,
            padding=10,
            ink=True,
            on_click=lambda e: open_add_recipe_dialog(category_name),
        )

        # Выбираем тело экрана (пустое состояние или сетка)
        if not recipes:
            content_view = ft.Column(
                [
                    ft.Icon(ft.Icons.MENU_BOOK, size=64, color=ft.Colors.GREY_400),
                    ft.Text(
                        "Здесь пока пусто",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "Запишите свой первый рецепт в эту категорию!",
                        size=14,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Записать рецепт",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE_400, color=ft.Colors.WHITE
                        ),
                        on_click=lambda e: open_add_recipe_dialog(category_name),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )
        else:
            grid = ft.GridView(
                expand=True,
                runs_count=2,
                max_extent=180,
                child_aspect_ratio=0.85,
                spacing=10,
                run_spacing=10,
                scroll=ft.ScrollMode.AUTO,
            )

            for recipe in recipes:
                grid.controls.append(build_recipe_card(recipe))

            grid.controls.append(add_card)
            content_view = grid

        # Собираем единый макет без двойных вызовов page.add
        category_layout = ft.Column(
            [
                header,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                content_view,
            ],
            expand=True,
            spacing=10,
        )

        page.navigation_bar = get_nav_bar(0)
        page.add(wrap_in_bounds(category_layout))
        page.update()

    # --- 4. ЭКРАН КОРЗИНЫ ---

    def show_cart_view():
        page.controls.clear()

        header = ft.Text("Корзина блюд", size=24, weight=ft.FontWeight.BOLD)
        cart_items = repo.get_cart_recipes_with_counts()

        def update_count(recipe_id, new_count):
            if new_count <= 0:
                repo.remove_from_cart(recipe_id)
            else:
                repo.add_to_cart(recipe_id, new_count)
            show_cart_view()

        if not cart_items:
            empty_state = ft.Column(
                [
                    ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=64, color=ft.Colors.GREY_400),
                    ft.Text("Корзина пуста", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    ft.Text("Добавляйте рецепты из категорий, чтобы сформировать меню!", size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
            page.add(wrap_in_bounds(ft.Column([header, ft.Divider(), empty_state], expand=True, spacing=10)))
        else:
            cart_list = ft.ListView(expand=True, spacing=10)

            for recipe, count in cart_items:
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(recipe.title, weight=ft.FontWeight.BOLD, size=16),
                                        ft.Text(f"⏱ {recipe.cooking_time} мин", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    expand=True
                                ),
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.Icons.REMOVE, 
                                            icon_size=18,
                                            on_click=lambda e, r_id=recipe.id, c=count: update_count(r_id, c - 1)
                                        ),
                                        ft.Text(f"{count}", weight=ft.FontWeight.BOLD, size=16),
                                        ft.IconButton(
                                            icon=ft.Icons.ADD, 
                                            icon_size=18,
                                            on_click=lambda e, r_id=recipe.id, c=count: update_count(r_id, c + 1)
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED_400,
                                    tooltip="Удалить из корзины",
                                    on_click=lambda e, r_id=recipe.id: update_count(r_id, 0)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    )
                )
                cart_list.controls.append(card)

            calc_button = ft.ElevatedButton(
                "Сформировать список покупок",
                icon=ft.Icons.CHECKLIST,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.ORANGE_500, 
                    color=ft.Colors.WHITE,
                    padding=15
                ),
                on_click=lambda e: show_shopping_list_view(),
                expand=True
            )

            page.add(wrap_in_bounds(ft.Column([header, ft.Divider(), cart_list, calc_button], expand=True, spacing=10)))

        page.navigation_bar = get_nav_bar(1)
        page.update()

    # --- 5. ЭКРАН РЕВИЗИИ И СПИСКА ПОКУПОК ---

    # --- 5. ЭКРАН РЕВИЗИИ И СПИСКА ПОКУПОК ---

    # --- 5. ЭКРАН РЕВИЗИИ И СПИСКА ПОКУПОК ---

    # --- 5. ЭКРАН РЕВИЗИИ И СПИСКА ПОКУПОК ---

    def format_amount(val: float) -> str:
        if val is None:
            return "0"
        if val.is_integer():
            return str(int(val))
        return str(round(val, 2))

    def show_shopping_list_view():
        page.controls.clear()

        is_shopping_mode = [False]
        shopping_raw = repo.calculate_shopping_list()
        
        shopping_state = {}
        for dept, items in shopping_raw.items():
            shopping_state[dept] = {}
            for (name, unit), amount in items.items():
                shopping_state[dept][(name, unit)] = {
                    "original_needed": amount,
                    "needed": amount,
                    "bought": False,
                    "in_cart": False
                }

        def refresh_ui():
            render_list()

        def open_have_dialog(dept, name, unit):
            item = shopping_state[dept][(name, unit)]
            current_needed = item["needed"]

            input_amt = ft.TextField(
                label=f"Сколько есть? ({unit})", 
                value=format_amount(current_needed),
                keyboard_type=ft.KeyboardType.NUMBER,
                autofocus=True
            )

            def cancel_dialog(e):
                item["bought"] = False
                dialog.open = False
                page.update()
                refresh_ui()

            def apply_partial(e):
                try:
                    have_val = float(input_amt.value.replace(",", "."))
                except ValueError:
                    have_val = 0.0

                remains = item["original_needed"] - have_val
                if remains <= 0:
                    item["needed"] = 0
                    item["bought"] = True
                else:
                    item["needed"] = round(remains, 2)
                    item["bought"] = False
                
                dialog.open = False
                page.update()
                refresh_ui()

            def apply_all_have(e):
                item["needed"] = 0
                item["bought"] = True
                dialog.open = False
                page.update()
                refresh_ui()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"{name}"),
                content=ft.Column(
                    [
                        ft.Text(f"Изначально нужно: {format_amount(item['original_needed'])} {unit}"),
                        ft.Container(height=5),
                        input_amt
                    ],
                    tight=True
                ),
                actions=[
                    ft.TextButton("Отмена", on_click=cancel_dialog),
                    ft.ElevatedButton(
                        "Учесть остаток", 
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_400, color=ft.Colors.WHITE),
                        on_click=apply_partial
                    ),
                    ft.ElevatedButton(
                        "Мы богаты (Всё есть)", 
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=apply_all_have
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        def toggle_item_home(dept, name, unit, is_checked):
            item = shopping_state[dept][(name, unit)]
            if is_checked:
                open_have_dialog(dept, name, unit)
            else:
                item["bought"] = False
                item["needed"] = item["original_needed"]
                refresh_ui()

        def toggle_item_shop(dept, name, unit, is_checked):
            shopping_state[dept][(name, unit)]["in_cart"] = is_checked
            refresh_ui()

        def finish_shopping_session(e):
            cart_raw = repo.get_cart_raw()
            for recipe_id in list(cart_raw.keys()):
                repo.remove_from_cart(recipe_id)
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Покупки завершены! Корзина очищена. Приятной готовки! 🍳"),
                bgcolor=ft.Colors.GREEN_700
            )
            page.snack_bar.open = True
            show_main_view()

        list_container = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=15)

        def switch_mode(to_shopping: bool):
            is_shopping_mode[0] = to_shopping
            refresh_ui()

        def render_list():
            page.controls.clear()
            list_container.controls.clear()

            in_shop = is_shopping_mode[0]
            header_title = "Список покупок 🛒" if in_shop else "А что есть дома? 🧊"

            header = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK, 
                        on_click=lambda e: switch_mode(False) if in_shop else show_cart_view(), 
                        tooltip="Назад"
                    ),
                    ft.Text(header_title, size=22, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START,
            )
            
            for dept, items in shopping_state.items():
                dept_cards = []
                
                for (name, unit), info in items.items():
                    needed = info["needed"]
                    original = info["original_needed"]
                    bought_home = info["bought"]
                    in_cart = info["in_cart"]

                    if in_shop and (bought_home or needed <= 0):
                        continue

                    if not in_shop:
                        is_partially_have = (needed < original) and not bought_home

                        if bought_home:
                            title_text = f"{name} (Всё есть)"
                        elif is_partially_have:
                            title_text = f"{name} — останется докупить {format_amount(needed)} {unit} (из {format_amount(original)})"
                        else:
                            title_text = f"{name} — {format_amount(needed)} {unit}"

                        cb = ft.Checkbox(
                            label=title_text,
                            value=bought_home or is_partially_have,
                            label_style=ft.TextStyle(
                                decoration=ft.TextDecoration.LINE_THROUGH if bought_home else ft.TextDecoration.NONE,
                                color=ft.Colors.GREY_500 if bought_home else ft.Colors.BLACK
                            ),
                            on_change=lambda e, d=dept, n=name, u=unit: toggle_item_home(d, n, u, e.control.value)
                        )
                    else:
                        title_text = f"{name} ({format_amount(needed)} {unit})"
                        cb = ft.Checkbox(
                            label=title_text,
                            value=in_cart,
                            label_style=ft.TextStyle(
                                decoration=ft.TextDecoration.LINE_THROUGH if in_cart else ft.TextDecoration.NONE,
                                color=ft.Colors.GREY_400 if in_cart else ft.Colors.BLACK
                            ),
                            on_change=lambda e, d=dept, n=name, u=unit: toggle_item_shop(d, n, u, e.control.value)
                        )

                    dept_cards.append(cb)

                if dept_cards:
                    dept_group = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(dept, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800, size=16),
                                ft.Divider(height=1),
                                *dept_cards
                            ],
                            spacing=8
                        ),
                        bgcolor=ft.Colors.WHITE,
                        padding=12,
                        border_radius=10,
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.GREY_200),
                            bottom=ft.BorderSide(1, ft.Colors.GREY_200),
                            left=ft.BorderSide(1, ft.Colors.GREY_200),
                            right=ft.BorderSide(1, ft.Colors.GREY_200),
                        )
                    )
                    list_container.controls.append(dept_group)

            if not in_shop:
                bottom_actions = ft.ElevatedButton(
                    "За покупками! 🛒",
                    icon=ft.Icons.SHOPPING_BAG,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, padding=15),
                    on_click=lambda e: switch_mode(True),
                    expand=True
                )
            else:
                bottom_actions = ft.Column(
                    [
                        ft.ElevatedButton(
                            "Теперь будем сыты, завершаем покупки! ✨",
                            icon=ft.Icons.CHECK_CIRCLE,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=15),
                            on_click=finish_shopping_session,
                            expand=True
                        ),
                        ft.OutlinedButton(
                            "Вернуться к ревизии «А что есть дома?»",
                            icon=ft.Icons.EDIT,
                            on_click=lambda e: switch_mode(False),
                            expand=True
                        ),
                    ],
                    spacing=8
                )

            page.add(wrap_in_bounds(ft.Column([header, ft.Divider(), list_container, bottom_actions], expand=True, spacing=10)))
            page.navigation_bar = get_nav_bar(1)
            page.update()

        render_list()

    # --- 6. ГЛАВНЫЙ ЭКРАН ---

    def show_main_view():
        page.controls.clear() # Полностью чистим страницу
        page.appbar = main_appbar

        header = ft.Text("Категории рецептов", size=22, weight=ft.FontWeight.BOLD)
        categories = repo.get_categories()

        def build_category_card(cat_name: str):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.RESTAURANT_MENU, size=32, color=ft.Colors.ORANGE_800),
                        ft.Text(cat_name, weight=ft.FontWeight.BOLD, size=15),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=12,
                padding=15,
                ink=True,
                on_click=lambda e, name=cat_name: show_category_view(name),
            )

        # Сетка категорий с включенной прокруткой
        categories_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=180,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            scroll=ft.ScrollMode.AUTO, # 👈 Добавляем скролл, чтобы ничего не налезало
        )

        for cat in categories:
            categories_grid.controls.append(build_category_card(cat))

        main_layout = ft.Column(
            [
                header, 
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT), 
                categories_grid
            ], 
            expand=True,
            spacing=10
        )

        page.navigation_bar = get_nav_bar(0)
        
        # Добавляем ТОЛЬКО один контейнер
        page.add(wrap_in_bounds(main_layout))
        page.update()

    show_main_view()

if __name__ == "__main__":
    ft.app(target=main)
