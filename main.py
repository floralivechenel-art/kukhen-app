import flet as ft
import uuid
import os
import sys
from storage.repository import RecipeRepository
from core.models import Recipe, Ingredient
from core.supabase_client import supabase  # <-- Добавили импорт Supabase

# ANDROID PERMISSIONS: Проверка и запрос разрешений на запуск
def request_android_permissions():
    """Запрашивает необходимые разрешения для работы на Android."""
    try:
        if hasattr(sys, 'mobile') or 'FLET_ANDROID' in os.environ:
            from android.permissions import request_permissions, Permission  # type: ignore

            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
    except ImportError:
        pass
    except Exception as e:
        print(f"Ошибка запроса разрешений: {e}")

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
    request_android_permissions()
    
    page.title = "KUKHEN — Личные рецепты"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 420
    page.window.height = 750
    page.padding = ft.Padding(left=15, top=12, right=15, bottom=24)

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    repo = RecipeRepository()

    # 1. ОБЕРТКА ДЛЯ ОГРАНИЧЕНИЯ ШИРИНЫ
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

    # Функция выхода из аккаунта
    def logout_click(e):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        page.client_storage.remove("supabase_session")
        show_auth_view()

    # Верхний плашка с кнопкой Выхода
    main_appbar = ft.AppBar(
        title=ft.Text("Kukhen", weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.ORANGE_50,
        actions=[
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                tooltip="Выйти из аккаунта",
                on_click=logout_click
            )
        ]
    )

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

    # --- 0. ЭКРАН АВТОРИЗАЦИИ / РЕГИСТРАЦИИ ---

    def show_auth_view():
        page.controls.clear()
        page.appbar = None
        page.navigation_bar = None

        email_tf = ft.TextField(
            label="Email",
            hint_text="user@example.com",
            width=320,
            keyboard_type=ft.KeyboardType.EMAIL,
            autofocus=True
        )
        password_tf = ft.TextField(
            label="Пароль",
            password=True,
            can_reveal_password=True,
            width=320
        )
        status_text = ft.Text(color=ft.Colors.RED_600, size=13, visible=False)

        # Переключатель режимов: Вход / Регистрация
        is_login_mode = [True]

        title_label = ft.Text("Вход в Kukhen", size=24, weight=ft.FontWeight.BOLD)
        action_button = ft.ElevatedButton("Войти", width=320, style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_500, color=ft.Colors.WHITE))
        switch_mode_btn = ft.TextButton("Нет аккаунта? Зарегистрироваться")

        def toggle_mode(e):
            is_login_mode[0] = not is_login_mode[0]
            if is_login_mode[0]:
                title_label.value = "Вход в Kukhen"
                action_button.text = "Войти"
                switch_mode_btn.text = "Нет аккаунта? Зарегистрироваться"
            else:
                title_label.value = "Регистрация"
                action_button.text = "Зарегистрироваться"
                switch_mode_btn.text = "Уже есть аккаунт? Войти"
            status_text.visible = False
            page.update()

        def handle_auth(e):
            email = email_tf.value.strip() if email_tf.value else ""
            password = password_tf.value.strip() if password_tf.value else ""

            if not email or not password:
                status_text.value = "Заполните Email и пароль!"
                status_text.color = ft.Colors.RED_600
                status_text.visible = True
                page.update()
                return

            status_text.value = "Подождите..."
            status_text.color = ft.Colors.BLUE_600
            status_text.visible = True
            page.update()

            try:
                if is_login_mode[0]:
                    # Вход
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.session:
                        page.client_storage.set("supabase_session", res.session.access_token)
                        repo.sync_from_cloud()
                        show_main_view()
                else:
                    # Регистрация
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    status_text.value = "Регистрация успешна! Теперь воидите."
                    status_text.color = ft.Colors.GREEN_600
                    status_text.visible = True
                    toggle_mode(None)
            except Exception as err:
                status_text.value = f"Ошибка: {err}"
                status_text.color = ft.Colors.RED_600
                status_text.visible = True
                page.update()

        action_button.on_click = handle_auth
        switch_mode_btn.on_click = toggle_mode

        auth_layout = ft.Column(
            [
                ft.Icon(ft.Icons.RESTAURANT_MENU, size=64, color=ft.Colors.ORANGE_500),
                title_label,
                ft.Container(height=10),
                email_tf,
                password_tf,
                status_text,
                ft.Container(height=10),
                action_button,
                switch_mode_btn,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )

        page.add(wrap_in_bounds(auth_layout))
        page.update()

    # --- 1. ФОРМА СОЗДАНИЯ / РЕДАКТИРОВАНИЯ РЕЦЕПТА ---

    def open_add_recipe_dialog(category_name: str, recipe_to_edit=None):
        known_ingredients = repo.get_known_ingredients()

        initial_title = recipe_to_edit.title if recipe_to_edit else ""
        initial_time = str(recipe_to_edit.cooking_time) if recipe_to_edit else "15"
        initial_comment = recipe_to_edit.comment if recipe_to_edit else ""

        title_input = ft.TextField(label="Название блюда", hint_text="Омлет с сыром", value=initial_title)
        time_input = ft.TextField(label="Время (мин)", keyboard_type=ft.KeyboardType.NUMBER, value=initial_time, width=120)
        comment_input = ft.TextField(label="Заметка к рецепту (необязательно)", hint_text="можно накормить табор", value=initial_comment, multiline=True, min_lines=1, max_lines=3)

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
            # Проходим по карточкам ингредиентов
            for card in ingredients_column.controls:
                try:
                    # Извлекаем поля прямо из структуры карточки
                    col_content = card.content.controls
                    
                    row1 = col_content[0].controls # [name_tf, delete_btn]
                    row2 = col_content[1].controls # [amount_tf, unit_dd]
                    dept_dd = col_content[2]       # dept_dd

                    name_val = row1[0].value.strip() if row1[0].value else ""
                    if name_val:
                        amt_str = row2[0].value.strip() if row2[0].value else "1"
                        try:
                            amt_val = float(amt_str.replace(",", "."))
                        except ValueError:
                            amt_val = 1.0

                        unit_val = row2[1].value or UNITS[0]
                        dept_val = dept_dd.value or DEPARTMENTS[0]

                        parsed_ingredients.append(
                            Ingredient(
                                name=name_val.capitalize(), 
                                amount=amt_val, 
                                unit=unit_val, 
                                category=dept_val
                            )
                        )
                except Exception as err:
                    print(f"Ошибка сбора ингредиента: {err}")

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

        def edit_recipe(e):
            close_viewer()
            open_add_recipe_dialog(category_name=recipe.category, recipe_to_edit=recipe)

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
            )

            for recipe in recipes:
                grid.controls.append(build_recipe_card(recipe))

            grid.controls.append(add_card)
            content_view = grid

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
        page.appbar = main_appbar

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

            calc_button = ft.Row(
                [
                    ft.ElevatedButton(
                        "Сформировать список покупок",
                        icon=ft.Icons.CHECKLIST,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE_500,
                            color=ft.Colors.WHITE,
                            padding=15,
                            shape=ft.RoundedRectangleBorder(radius=10)
                        ),
                        on_click=lambda e: show_shopping_list_view(),
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )

            cart_list.expand = True 

            page.add(wrap_in_bounds(ft.Column([header, ft.Divider(), cart_list, calc_button], expand=True, spacing=10)))

        page.navigation_bar = get_nav_bar(1)
        page.update()

    # --- 5. ЭКРАН РЕВИЗИИ И СПИСКА ПОКУПОК ---

    def show_shopping_list_view():
        page.controls.clear()
        page.appbar = main_appbar

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
                    "in_cart": False,
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
                autofocus=True,
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
                        input_amt,
                    ],
                    tight=True,
                ),
                actions=[
                    ft.TextButton("Отмена", on_click=cancel_dialog),
                    ft.ElevatedButton(
                        "Учесть остаток",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_400, color=ft.Colors.WHITE),
                        on_click=apply_partial,
                    ),
                    ft.ElevatedButton(
                        "Мы богаты (Всё есть)",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                        on_click=apply_all_have,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
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
                bgcolor=ft.Colors.GREEN_700,
            )
            page.snack_bar.open = True
            show_main_view()

        list_container = ft.ListView(expand=True, spacing=15)

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
                        tooltip="Назад",
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
                                color=ft.Colors.GREY_500 if bought_home else ft.Colors.BLACK,
                            ),
                            on_change=lambda e, d=dept, n=name, u=unit: toggle_item_home(d, n, u, e.control.value),
                        )
                    else:
                        title_text = f"{name} ({format_amount(needed)} {unit})"
                        cb = ft.Checkbox(
                            label=title_text,
                            value=in_cart,
                            label_style=ft.TextStyle(
                                decoration=ft.TextDecoration.LINE_THROUGH if in_cart else ft.TextDecoration.NONE,
                                color=ft.Colors.GREY_400 if in_cart else ft.Colors.BLACK,
                            ),
                            on_change=lambda e, d=dept, n=name, u=unit: toggle_item_shop(d, n, u, e.control.value),
                        )

                    dept_cards.append(cb)

                if dept_cards:
                    dept_group = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(dept, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800, size=16),
                                ft.Divider(height=1),
                                *dept_cards,
                            ],
                            spacing=8,
                        ),
                        bgcolor=ft.Colors.WHITE,
                        padding=12,
                        border_radius=10,
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.GREY_200),
                            bottom=ft.BorderSide(1, ft.Colors.GREY_200),
                            left=ft.BorderSide(1, ft.Colors.GREY_200),
                            right=ft.BorderSide(1, ft.Colors.GREY_200),
                        ),
                    )
                    list_container.controls.append(dept_group)

            if not in_shop:
                bottom_actions = ft.Row(
                    [
                        ft.ElevatedButton(
                            "За покупками! 🛒",
                            icon=ft.Icons.SHOPPING_BAG,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN_600,
                                color=ft.Colors.WHITE,
                                padding=15,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            on_click=lambda e: switch_mode(True),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            else:
                bottom_actions = ft.Column(
                    [
                        ft.ElevatedButton(
                            "Теперь будем сыты, завершаем покупки! ✨",
                            icon=ft.Icons.CHECK_CIRCLE,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN_700,
                                color=ft.Colors.WHITE,
                                padding=15,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            on_click=finish_shopping_session,
                        ),
                        ft.OutlinedButton(
                            "Вернуться к ревизии «А что есть дома?»",
                            icon=ft.Icons.EDIT,
                            style=ft.ButtonStyle(
                                padding=12,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            on_click=lambda e: switch_mode(False),
                        ),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                )

            page.add(wrap_in_bounds(ft.Column([header, ft.Divider(), list_container, bottom_actions], expand=True, spacing=10)))
            page.navigation_bar = get_nav_bar(1)
            page.update()

        render_list()

    # --- 6. ГЛАВНЫЙ ЭКРАН ---

    def show_main_view():
        page.controls.clear()
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

        categories_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=180,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
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
        page.add(wrap_in_bounds(main_layout))
        page.update()

    # --- ТОЧКА ВХОДА И ПРОВЕРКА СЕССИИ ---

    saved_token = page.client_storage.get("supabase_session")
    if saved_token:
        try:
            # Восстанавливаем авторизацию
            supabase.auth.set_session(saved_token, refresh_token="")
            repo.sync_from_cloud()
            show_main_view()
        except Exception:
            # Если сессия устарела или произошел сбой — просим залогиниться
            show_auth_view()
    else:
        show_auth_view()

if __name__ == "__main__":
    ft.app(target=main)
