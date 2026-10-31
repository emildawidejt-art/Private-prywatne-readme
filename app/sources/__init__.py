from importlib import import_module

IDS = ['olx', 'otomoto', 'sprzedajemy', 'allegro', 'gratka', 'mascus_pl', 'machineryline_pl', 'truck1', 'skelbiu', 'autoplius', 'autogidas', 'mascus_lt', 'machineryline_lt', 'facebook']
SOURCES = {i: import_module(f"app.sources.{i}").SOURCE for i in IDS}
