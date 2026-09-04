# ui/auth_view.py
import flet as ft
from core.supabase_client import supabase

def auth_view(page: ft.Page, on_auth_success):
    email_input = ft.TextField(label="Email", width=300)
    password_input = ft.TextField(label="Пароль", password=True, can_reveal_password=True, width=300)
    error_text = ft.Text(color="red", visible=False)

    def login_click(e):
        try:
            # 1. Отправляем логин/пароль в Supabase
            res = supabase.auth.sign_in_with_password({
                "email": email_input.value,
                "password": password_input.value
            })
            
            # 2. Сохраняем сессию в память телефона через Flet
            page.client_storage.set("supabase_session", res.session.access_token)
            
            # 3. Переходим в главное приложение
            on_auth_success()
        except Exception as err:
            error_text.value = f"Ошибка входа: {err}"
            error_text.visible = True
            page.update()

    def register_click(e):
        try:
            # Регистрация нового пользователя
            res = supabase.auth.sign_up({
                "email": email_input.value,
                "password": password_input.value
            })
            page.snack_bar = ft.SnackBar(ft.Text("Регистрация успешна! Теперь нажмите 'Войти'"))
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            error_text.value = f"Ошибка регистрации: {err}"
            error_text.visible = True
            page.update()

    return ft.View(
        "/auth",
        [
            ft.Column(
                [
                    ft.Text("Вход в Книгу Рецептов", size=24, weight=ft.FontWeight.BOLD),
                    email_input,
                    password_input,
                    error_text,
                    ft.ElevatedButton("Войти", on_click=login_click, width=300),
                    ft.OutlinedButton("Зарегистрироваться", on_click=register_click, width=300),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]
    )