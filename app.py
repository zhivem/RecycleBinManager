import ctypes
import sys
import os
import autostart
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtCore import QTimer, QSettings
from toggle_recycle_bin import toggle_show_recycle_bin, is_recycle_bin_visible
from icon_manager import IconManager 

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]

CSIDL_BITBUCKET = 0x000a

# Инициализация настроек
settings = QSettings("RecycleBinManager", "RecycleManager")
icon_manager = IconManager(settings)

def show_notification(title, message, icon_name=None, is_main=True):
    """
    Отображает системное уведомление с указанными параметрами.
    """
    if settings.value("show_notifications", True, type=bool):
        if icon_name:
            if is_main:
                icon = icon_manager.load_main_icon(icon_name)
            else:
                icon = icon_manager.load_common_icon(icon_name)
        else:
            icon = QIcon()
        tray_icon.showMessage(title, message, icon, 5000)

def empty_recycle_bin():
    """
    Очищает корзину и отображает уведомление о результате.
    """
    try:
        SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
        flags = 0x01
        bin_path = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_BITBUCKET, 0, 0, bin_path)
        result = SHEmptyRecycleBin(None, bin_path.value, flags)

        if result == 0 or result == -2147418113:
            show_notification("Корзина", "Корзина успешно очищена.", "recycle-empty.ico")
        else:
            show_notification(
                "Корзина",
                f"Произошла ошибка при очистке корзины. Код ошибки: {result}",
                "recycle-full.ico",
            )

        update_icon()
    except Exception as e:
        print(f"Ошибка при очистке корзины: {e}")
        show_notification("Ошибка", f"Не удалось очистить корзину: {e}", "recycle-full.ico")

def open_recycle_bin():
    """
    Открывает окно корзины.
    """
    try:
        os.startfile("shell:RecycleBinFolder")
    except Exception as e:
        print(f"Ошибка при открытии корзины: {e}")
        show_notification("Ошибка", f"Не удалось открыть корзину: {e}", "recycle-full.ico")

def exit_program():
    """
    Завершает работу приложения.
    """
    QApplication.quit()

def get_recycle_bin_info():
    """
    Получаем информацию о корзине: количество элементов и общий размер.
    """
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))

    if result != 0:
        show_notification("Ошибка", "Не удалось получить состояние корзины.", "recycle-full.ico")
        return None, None

    num_items = rbinfo.i64NumItems
    total_size = rbinfo.i64Size

    return num_items, total_size

def format_size(bytes_size):
    """
    Намутим перевод в КВ, МБ, GB, TB
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    bytes_size /= 1024  # Переводим в KB
    if bytes_size < 1024:
        return f"{bytes_size:.1f} KB"
    bytes_size /= 1024  # Переводим в MB
    if bytes_size < 1024:
        return f"{bytes_size:.0f} MB"
    bytes_size /= 1024  # Переводим в GB
    if bytes_size < 1024:
        return f"{bytes_size:.0f} GB"
    bytes_size /= 1024  # Переводим в TB
    return f"{bytes_size:.2f} TB"

def update_icon():
    """
    Обновляет иконку в системном трее в зависимости от состояния корзины.
    Также обновляет тултип с количеством элементов и размером.
    """
    num_items, total_size = get_recycle_bin_info()
    if num_items is None:
        # Если произошла ошибка, используем стандартный тултип
        tray_icon.setIcon(icon_manager.load_main_icon("recycle-full.ico"))
        tray_icon.setToolTip("Менеджер Корзины")
        return

    if num_items == 0:
        tray_icon.setIcon(icon_manager.load_main_icon("recycle-empty.ico"))
    else:
        tray_icon.setIcon(icon_manager.load_main_icon("recycle-full.ico"))

    # Форматируем размер для отображения
    size_str = format_size(total_size)
    tray_icon.setToolTip(f"Менеджер Корзины\nЭлементов: {num_items}\nЗанято: {size_str}")

def is_recycle_bin_empty():
    """
    Проверяет, пуста ли корзина.
    """
    num_items, _ = get_recycle_bin_info()
    if num_items is None:
        return False
    return num_items == 0

def periodic_update():
    """
    Периодически обновляет иконку и тултип в трее.
    """
    update_icon()

def toggle_autostart(checked):
    """
    Включает или отключает автозапуск приложения.
    """
    if checked:
        success = autostart.enable_autostart()
        if success:
            show_notification("Автозапуск", "Автозапуск включен.", "autostart-enabled.ico", is_main=False)
        else:
            show_notification("Автозапуск", "Не удалось включить автозапуск.", "autostart-disabled.ico", is_main=False)
            autostart_action.setChecked(False)
    else:
        success = autostart.disable_autostart()
        if success:
            show_notification("Автозапуск", "Автозапуск отключен.", "autostart-disabled.ico", is_main=False)
        else:
            show_notification("Автозапуск", "Не удалось отключить автозапуск.", "autostart-enabled.ico", is_main=False)
            autostart_action.setChecked(True)

def toggle_show_notifications(checked):
    """
    Включает или отключает показ уведомлений.
    """
    settings.setValue("show_notifications", checked)
    if checked:
        show_notification("Уведомления", "Уведомления включены.", "notifications-enabled.ico", is_main=False)

def initialize_autostart_menu():
    """
    Инициализирует меню автозапуска.
    """
    global autostart_action
    autostart_action = QAction("Автозапуск", checkable=True)
    autostart_action.setChecked(autostart.is_autostart_enabled())
    autostart_action.triggered.connect(toggle_autostart)
    tray_menu.addAction(autostart_action)

def initialize_notifications_menu():
    """
    Инициализирует меню уведомлений.
    """
    global show_notifications_action
    show_notifications_action = QAction("Показывать уведомления", checkable=True)
    show_notifications_action.setChecked(settings.value("show_notifications", True, type=bool))
    show_notifications_action.triggered.connect(toggle_show_notifications)
    tray_menu.addAction(show_notifications_action)

    # Добавляем разделитель после основных действий
    tray_menu.addSeparator()

def initialize_show_recycle_bin_menu():
    """
    Инициализирует меню отображения корзины на рабочем столе.
    """
    global show_recycle_bin_action
    is_visible = is_recycle_bin_visible()
    show_recycle_bin_action = QAction("Отображать 🗑️ на рабочем столе", checkable=True)
    show_recycle_bin_action.setChecked(is_visible)
    show_recycle_bin_action.triggered.connect(lambda checked: toggle_show_recycle_bin(checked))
    tray_menu.addAction(show_recycle_bin_action)

    # Добавляем разделитель после основных действий
    tray_menu.addSeparator()

def initialize_icon_set_menu():
    """
    Инициализирует меню выбора набора иконок.
    """
    icon_set_menu = QMenu("Выбрать набор иконок", tray_menu)
    available_icon_sets = icon_manager.get_available_icon_sets()

    # Создаём QActionGroup для управления выбором набора иконок
    icon_set_group = QActionGroup(icon_set_menu)
    icon_set_group.setExclusive(True)

    current_set = icon_manager.get_current_icon_set()

    for icon_set in available_icon_sets:
        # Загружаем иконку 'full' для предпросмотра
        icon_path = f"icons/icon_sets/{icon_set}/recycle-full.ico"
        try:
            icon = QIcon(icon_manager.resource_path(icon_path))
        except Exception as e:
            print(f"Ошибка при загрузке иконки для набора '{icon_set}': {e}")
            icon = QIcon()

        # Создаём стандартный QAction для каждого набора иконок
        action = QAction(icon_set, icon=icon, checkable=True, parent=icon_set_group)
        action.setData(icon_set)  # Сохраняем имя набора иконок в данных действия

        # Устанавливаем действие как отмеченное, если это текущий набор
        if icon_set == current_set:
            action.setChecked(True)

        # Подключаем слот для установки набора иконок при выборе
        action.triggered.connect(lambda checked, set_name=icon_set: set_icon_set(set_name))

        # Добавляем действие в группу и меню
        icon_set_group.addAction(action)
        icon_set_menu.addAction(action)

    tray_menu.addMenu(icon_set_menu)

def set_icon_set(set_name):
    """
    Устанавливает выбранный набор иконок и обновляет интерфейс.
    """
    icon_manager.set_icon_set(set_name)
    update_icon()
    show_notification("Набор иконок", f"Выбран набор иконок: {set_name}")

def on_tray_icon_activated(reason):
    """
    Обрабатывает активацию иконки в трее (например, двойной клик).
    """
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        open_recycle_bin()

if __name__ == "__main__":
    print(f"Текущая рабочая директория: {Path.cwd()}")

    if os.name != 'nt':
        print("Это приложение работает только на Windows.")
        sys.exit(1)

    try:
        icon_manager.verify_icons()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    app = QApplication(sys.argv)

    # Создаём системный трей-иконку
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(icon_manager.load_main_icon("recycle-empty.ico"))

    # Создаём контекстное меню для трея
    tray_menu = QMenu()
    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    exit_action = QAction("Выход", triggered=exit_program)

    tray_menu.addAction(open_action)
    tray_menu.addAction(empty_action)

    # Добавляем разделитель после основных действий
    tray_menu.addSeparator()

    # Инициализируем остальные пункты меню
    initialize_autostart_menu()
    initialize_notifications_menu()
    initialize_show_recycle_bin_menu()
    initialize_icon_set_menu()

    # Добавляем разделитель перед выходом
    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Менеджер Корзины")
    tray_icon.show()

    tray_icon.activated.connect(on_tray_icon_activated)

    # Запускаем таймер для периодического обновления иконки и тултипа
    timer = QTimer()
    timer.timeout.connect(periodic_update)
    timer.start(1000)

    sys.exit(app.exec())
