import ctypes
import winreg

def toggle_show_recycle_bin(checked):
    """
    Включает или отключает отображение корзины на рабочем столе.
    """
    try:
        # Ключ реестра для управления отображением корзины
        reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"
        reg_value_name = "{645FF040-5081-101B-9F08-00AA002F954E}"  # GUID для корзины

        # Подключаемся к реестру
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path, 0, winreg.KEY_SET_VALUE) as key:
            if checked:
                # 0 означает, что корзина отображается
                winreg.SetValueEx(key, reg_value_name, 0, winreg.REG_DWORD, 0)
            else:
                # 1 скрывает корзину
                winreg.SetValueEx(key, reg_value_name, 0, winreg.REG_DWORD, 1)

        # Обновляем рабочий стол
        ctypes.windll.shell32.SHChangeNotify(0x8000000, 0x1000, None, None)
        print(f"Состояние отображения корзины изменено: {'Отображать' if checked else 'Скрыть'}")
    except Exception as e:
        print(f"Ошибка при переключении отображения корзины: {e}")

def is_recycle_bin_visible():
    """
    Проверяет текущее состояние отображения корзины.
    """
    try:
        reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"
        reg_value_name = "{645FF040-5081-101B-9F08-00AA002F954E}"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, reg_value_name)
            return value == 0  # 0 означает отображение
    except FileNotFoundError:
        return True  # Если значение отсутствует, по умолчанию корзина отображается
    except Exception as e:
        print(f"Ошибка при чтении состояния отображения корзины: {e}")
        return True
