import ctypes
from ctypes import c_int, byref, sizeof, Structure, POINTER
from ctypes.wintypes import DWORD, HWND, ULONG

class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", DWORD),
        ("AccentFlags", DWORD),
        ("GradientColor", DWORD),
        ("AnimationId", DWORD)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attribute", DWORD),
        ("Data", POINTER(ACCENT_POLICY)),
        ("SizeOfData", ULONG)
    ]

# Accent States
ACCENT_DISABLED = 0
ACCENT_ENABLE_GRADIENT = 1
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4 # Windows 10 1803+
ACCENT_INVALID_STATE = 5

class WindowEffect:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        
        # Load SetWindowCompositionAttribute
        self.SetWindowCompositionAttribute = self.user32.SetWindowCompositionAttribute
        self.SetWindowCompositionAttribute.argtypes = [HWND, POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
        self.SetWindowCompositionAttribute.restype = c_int

    def apply_acrylic(self, hwnd, gradient_color=0x01FFFFFF):
        """
        Apply Acrylic Blur effect to the window.
        hwnd: Window Handle (int)
        gradient_color: ABGR integer (e.g. 0xCCFFFFFF for white tint with transparency)
        """
        try:
            accent = ACCENT_POLICY()
            accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
            accent.GradientColor = gradient_color
            
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19 # WCA_ACCENT_POLICY
            data.Data = ctypes.pointer(accent)
            data.SizeOfData = sizeof(accent)
            
            self.SetWindowCompositionAttribute(int(hwnd), byref(data))
            return True
        except Exception as e:
            print(f"Failed to apply acrylic: {e}")
            return False

    def disable_effect(self, hwnd):
        try:
            accent = ACCENT_POLICY()
            accent.AccentState = ACCENT_DISABLED
            
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19
            data.Data = ctypes.pointer(accent)
            data.SizeOfData = sizeof(accent)
            
            self.SetWindowCompositionAttribute(int(hwnd), byref(data))
        except:
            pass
