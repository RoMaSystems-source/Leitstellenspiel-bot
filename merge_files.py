#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge bot.py into bot_gui_new.py to create a standalone file
"""

# Lese bot.py
with open('bot.py', 'r', encoding='utf-8') as f:
    bot_content = f.read()

# Lese bot_gui_new.py
with open('bot_gui_new.py', 'r', encoding='utf-8') as f:
    gui_content = f.read()

# Finde wo die BotGUI Klasse startet
bot_gui_start = gui_content.find('\nclass BotGUI:')

# Nehme alles von bot.py ab "class LeitstellenspielBot"
bot_class_start = bot_content.find('\nclass LeitstellenspielBot:')
bot_to_insert = bot_content[bot_class_start:]

# Erstelle neue Datei: GUI-Header + Bot-Klasse + GUI-Klasse
new_content = gui_content[:bot_gui_start] + bot_to_insert + '\n' + gui_content[bot_gui_start:]

# Schreibe neue Datei
with open('bot_standalone.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✓ bot_standalone.py erstellt!')
print(f'  Größe: {len(new_content)} Zeichen')

