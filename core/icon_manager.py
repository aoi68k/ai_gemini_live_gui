import os
import urllib.request
import tkinter as tk
from core import config

ICON_DIR = os.path.join(config.BASE_DIR, "data", "icons")

_icon_cache = {}

def get_icon(hex_code, size_factor=4):
    """
    Downloads and caches a Twemoji icon.
    size_factor=4 means subsample 72x72 by 4 -> 18x18
    """
    if hex_code in _icon_cache:
        return _icon_cache[hex_code]
        
    os.makedirs(ICON_DIR, exist_ok=True)
    icon_path = os.path.join(ICON_DIR, f"{hex_code}.png")
    
    if not os.path.exists(icon_path):
        url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{hex_code}.png"
        try:
            urllib.request.urlretrieve(url, icon_path)
        except Exception as e:
            print(f"Failed to download icon {hex_code}: {e}")
            return ""
            
    try:
        img = tk.PhotoImage(file=icon_path)
        if size_factor > 1:
            img = img.subsample(size_factor, size_factor)
        _icon_cache[hex_code] = img
        return img
    except Exception as e:
        print(f"Failed to load icon {hex_code}: {e}")
        return ""

def get_character_icon(filename, target_size=(40, 40)):
    if not filename:
        return ""
    cache_key = f"char_{filename}_{target_size[0]}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
        
    icon_path = os.path.join(ICON_DIR, filename)
    if not os.path.exists(icon_path):
        return ""
        
    try:
        from PIL import Image, ImageTk
        img = Image.open(icon_path).convert("RGBA")
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        _icon_cache[cache_key] = tk_img
        return tk_img
    except Exception as e:
        print(f"Failed to load character icon {filename}: {e}")
        return ""

def create_icon_dropdown(parent, icon_var, icon_files):
    import tkinter as tk
    from tkinter import ttk
    mb = ttk.Menubutton(parent, text=icon_var.get() or "(なし)", direction="below")
    menu = tk.Menu(mb, tearoff=0)
    mb.config(menu=menu)
    
    def _on_select(filename):
        icon_var.set(filename)
        img = get_character_icon(filename, target_size=(24, 24)) if filename else None
        if img:
            mb.config(text=f" {filename}", image=img, compound=tk.LEFT)
        else:
            mb.config(text=filename or "(なし)", image="", compound=tk.NONE)
            
    menu.add_command(label="(なし)", command=lambda: _on_select(""))
    for i, f in enumerate(icon_files):
        img = get_character_icon(f, target_size=(24, 24))
        cbreak = 1 if i > 0 and i % 15 == 0 else 0
        if img:
            menu.add_command(label=f" {f}", image=img, compound=tk.LEFT, command=lambda name=f: _on_select(name), columnbreak=cbreak)
        else:
            menu.add_command(label=f, command=lambda name=f: _on_select(name), columnbreak=cbreak)
            
    _on_select(icon_var.get())
    return mb
