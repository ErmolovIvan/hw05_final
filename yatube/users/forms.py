from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class CreationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'email')
