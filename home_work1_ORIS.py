class Playlist:
    SOUND = [
        {"name": "Bohemian Rhapsody", "duration": 354},
        {"name": "Stairway to Heaven", "duration": 482},
        {"name": "Imagine", "duration": 183},
        {"name": "Smells Like Teen Spirit", "duration": 301},
        {"name": "Hotel California", "duration": 391},
    ]
    def __init__(self):
        self.songs = self.SOUND.copy()

    def add_song(self, name, duration):
        self.songs.append({"name": name, "duration": duration})
        print(f'Песян "{name}" добавлена')
        print()

    def remove_song(self, name):
        for i, song in enumerate(self.songs):
            if song['name'].lower() == name.lower():
                del self.songs[i]
                print(f'Песня "{name}" удалена')
                print()
                return
        print(f'Песня "{name}" не найдена')
        print()
    def total_duration(self):
        cnt = 0
        for song in self.songs:
            cnt += song["duration"]
        print()
        return cnt


    def __len__(self):
        return len(self.songs)

    def show_list_sound(self):
        if not self.songs:
            print("Плейлист пустой!")
            print()
            return
        for ids, song in enumerate(self.songs, start=1):
            mn = song["duration"] // 60 # Минуты для красивого вывода
            sc = song["duration"] % 60 # Секунды для красивого вывода
            print(f'{ids}. {song["name"]} - длительность {mn}:{sc:02d}')
        print() #Добавил пустые принты после каждой функции, без пустой строки выглядит сплющено и однотонно

pl = Playlist()

pl.show_list_sound()

print(f'Общая длительность: {pl.total_duration()}')# Получение общей продолжительности
print(f"Количество песен: {len(pl)}\n") # Получение количества песен

pl.remove_song('Bohemian Rhapsody') # - удаление существующей песни
pl.remove_song('Той зимой недалекой') # - попытка удалить песню, которой нет

pustoy = Playlist()
for pusto in pustoy.songs[:]:
    pustoy.remove_song(pusto["name"])
pustoy.show_list_sound() # - пустой плейлист

pl.add_song("Той зимой недалекой", "217")
pl.add_song("Над Москва-Рекой", "398") # - добавление нескольких песен

pl1 = Playlist()# - удаление песни из плейлиста с несколькими песнями
pl1.remove_song('Imagine')
pl1.show_list_sound()

pl1.remove_song('Bohemian Rhapsody')
pl1.show_list_sound()

pl1.remove_song('Hotel California')
pl1.show_list_sound()

