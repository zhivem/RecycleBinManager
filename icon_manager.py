import sys
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSettings

class IconManager:
    def __init__(self, settings: QSettings):
        """
        Инициализирует менеджер иконок с использованием предоставленных настроек.
        """
        self.settings = settings

    @staticmethod
    def resource_path(relative_path):
        """
        Получает полный путь к ресурсу, работает как в режиме разработки, так и в собранном приложении.
        """
        try:
            base_path = Path(sys._MEIPASS)
        except AttributeError:
            base_path = Path(__file__).parent
        full_path = base_path / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Ресурс не найден: {full_path}")
        return str(full_path)

    def get_current_icon_set(self):
        """
        Возвращает текущий выбранный набор иконок, по умолчанию 'default'.
        """
        return self.settings.value("icon_set", "default")

    def load_main_icon(self, icon_name):
        """
        Загружает основную иконку из выбранного набора иконок.
        """
        icon_set = self.get_current_icon_set()
        icon_path = f"icons/icon_sets/{icon_set}/{icon_name}"
        full_icon_path = self.resource_path(icon_path)
        print(f"Попытка загрузить основную иконку по пути: {full_icon_path}")
        try:
            return QIcon(full_icon_path)
        except Exception as e:
            print(f"Ошибка при загрузке основной иконки: {e}")
            return QIcon()

    def load_common_icon(self, icon_name):
        """
        Загружает общую иконку из папки common.
        """
        icon_path = f"icons/common/{icon_name}"
        full_icon_path = self.resource_path(icon_path)
        print(f"Попытка загрузить общую иконку по пути: {full_icon_path}")
        try:
            return QIcon(full_icon_path)
        except Exception as e:
            print(f"Ошибка при загрузке общей иконки: {e}")
            return QIcon()

    def get_available_icon_sets(self):
        """
        Возвращает список доступных наборов иконок.
        """
        icons_dir = Path(self.resource_path("icons/icon_sets"))
        icon_sets = [p.name for p in icons_dir.iterdir() if p.is_dir()]
        return icon_sets

    def set_icon_set(self, set_name):
        """
        Устанавливает выбранный набор иконок и обновляет настройки.
        """
        self.settings.setValue("icon_set", set_name)
        # Предполагается, что метод обновления иконки будет вызван отдельно

    def verify_icons(self):
        """
        Проверяет наличие всех необходимых иконок в наборах иконок и общей папке.
        """
        # Проверка основных иконок
        icon_sets = self.get_available_icon_sets()
        required_main_icons = ["recycle-empty.ico", "recycle-full.ico"]

        for icon_set in icon_sets:
            for icon in required_main_icons:
                icon_full_path = Path(self.resource_path(f"icons/icon_sets/{icon_set}/{icon}"))
                if not icon_full_path.exists():
                    print(f"Основная иконка не найдена: {icon_full_path}")
                    raise FileNotFoundError(f"Основная иконка не найдена: {icon_full_path}")
                else:
                    print(f"Основная иконка найдена: {icon_full_path}")

        # Проверка общих иконок
        required_common_icons = [
            "autostart-enabled.ico",
            "autostart-disabled.ico",
            "notifications-enabled.ico",
        ]

        for icon in required_common_icons:
            icon_full_path = Path(self.resource_path(f"icons/common/{icon}"))
            if not icon_full_path.exists():
                print(f"Общая иконка не найдена: {icon_full_path}")
                raise FileNotFoundError(f"Общая иконка не найдена: {icon_full_path}")
            else:
                print(f"Общая иконка найдена: {icon_full_path}")
