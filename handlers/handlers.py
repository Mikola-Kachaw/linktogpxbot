import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
import requests
import time
from bs4 import BeautifulSoup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config_data.config import Config, load_config
from aiogram.types.input_file import FSInputFile

from database.database import insert_database
from keyboards.keyboard import html_keyboard
from lexicon.lexicon import LEXICON_RU

config: Config = load_config()
bot = Bot(token=config.tg_bot.token)

class Link(StatesGroup):
    link = State()
router = Router()

@router.message(Command(commands=['start']))
async def process_start_command(message: Message):
    await message.answer(f"<b>Привет, {message.from_user.full_name}!👀</b>", parse_mode="HTML")
    await message.answer(LEXICON_RU['/start'],
    reply_markup = html_keyboard)

@router.message(F.text == 'Начать конвертацию')
async def get_link(message: Message, state: FSMContext):
    await state.set_state(Link.link)
    await message.answer('Введите ссылку на страницу:')
@router.message(Link.link)
async def get_link_2(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    link = message.text
    await state.update_data(link=link)
    await message.reply("Обрабатываю запрос...")
    time.sleep(1)
    data = await state.get_data()
    link = data.get("link")
    insert_database(user_id, username, link)

    if link:
        try:
            def fetch_data(link):
                count = 0
                while True:
                    response = requests.get(link)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    scripts = soup.find_all('script', class_="state-view")

                    if scripts:
                        return scripts[0].string  # Предполагаем, что нужные данные в первом найденном скрипте

                    count += 1
                    print(count)
            def extract_coordinates(content, output_file):
                start_marker = '"coordinates":[['
                end_marker = ']]}'

                start_index = content.find(start_marker)
                end_index = content.find(end_marker, start_index)

                if start_index != -1 and end_index != -1:
                    start_index += len(start_marker)
                    coordinates_data = content[start_index:end_index].strip()

                    # Убираем квадратные скобки и запятые, а затем разбиваем на строки
                    coordinates_data = coordinates_data.replace('[', '').replace(']', '').replace(',', '\n').strip()

                    with open(output_file, 'w', encoding='utf-8') as outfile:
                        outfile.write(coordinates_data)
                else:
                    print("Не удалось найти координаты в данных.")

            def edit_file(search_string, file_name):
                with open(file_name, 'r', encoding="utf-8") as file:
                    lines = file.readlines()

                filtered_lines = [line for line in lines if search_string in line]

                if filtered_lines:
                    with open(file_name, 'w', encoding="utf-8") as file:
                        file.writelines(filtered_lines)
                else:
                    print("Строки не найдены.")

            # Основной код
            file_name = f"./database/{message.from_user.username}.txt"

            # Получаем данные с URL
            data = fetch_data(link)

            # Записываем полученные данные в файл
            with open(file_name, 'w', encoding="utf-8") as file:
                file.write(data)

            # Извлекаем координаты из файла
            extract_coordinates(data, file_name)

            import xml.etree.ElementTree as ET

            import xml.etree.ElementTree as ET

            def convert_to_gpx(input_file, output_file):
                # Создаем корневой элемент GPX
                gpx = ET.Element('gpx', version='1.1', creator='YourName')

                # Создаем элемент track
                trk = ET.SubElement(gpx, 'trk')
                trkseg = ET.SubElement(trk, 'trkseg')  # Создаем сегмент трека

                with open(input_file, 'r') as file:
                    lines = file.readlines()

                    # Обрабатываем координаты
                    for i in range(0, len(lines), 2):  # Проходим по строкам с шагом 2
                        if i + 1 < len(lines):  # Проверяем, чтобы не выйти за пределы списка
                            longitude = lines[i].strip()  # Долгота
                            latitude = lines[i + 1].strip()  # Широта

                            # Создаем элемент "trkpt" (track point) для каждой пары координат
                            trkpt = ET.SubElement(trkseg, 'trkpt', lat=latitude, lon=longitude)
                            ET.SubElement(trkpt, 'name').text = f'Point {i // 2 + 1}'  # Имя точки

                # Записываем GPX в файл
                tree = ET.ElementTree(gpx)
                tree.write(output_file, encoding='utf-8', xml_declaration=True)

            # Основной код
            input_file = f'./database/{message.from_user.username}.txt'  # Имя входного текстового файла с координатами
            output_file = f'./database/{message.from_user.username}.gpx'  # Имя выходного GPX файла

            convert_to_gpx(input_file, output_file)
            user_id = message.from_user.id
            document = FSInputFile(f'./database/{message.from_user.username}.gpx')
            await bot.send_document(user_id, document, caption=f'Ваш GPX-файл!')
            os.remove(f'./database/{message.from_user.username}.txt')
        except Exception as e:
            await message.answer(f'Произошла ошибка при получении информации: {str(e)}')
    else:
        await message.answer('Пожалуйста, сначала введите ссылку на страницу.')
    await state.clear()

# Обработчик команды /help
@router.message(Command(commands=["help"]))
async def start_command(message:Message):
    await message.answer(text=LEXICON_RU['/help'], reply_markup=html_keyboard, parse_mode="HTML")