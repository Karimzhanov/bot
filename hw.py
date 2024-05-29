import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)

TOKEN = '7087985384:AAE9hwCLgmhi9UEB1HA97stZZAAxXX4Q0aA'
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

DATABASE_URL = "sqlite:///hotels.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String, index=True)
    city = Column(String, index=True)
    accommodation_type = Column(String)
    rooms_count = Column(Integer)
    amenities = Column(Text)
    distance_beach = Column(String)
    price_range = Column(String)
    photo_ids = Column(Text)
    photo_descriptions = Column(Text)


Base.metadata.create_all(bind=engine)


class Registration(StatesGroup):
    ACCOUNT_TYPE = State()


class BusinessRegistration(StatesGroup):
    REGION = State()
    CITY = State()
    ACCOMMODATION_TYPE = State()
    ROOMS_COUNT = State()
    AMENITIES_NUTRITION = State()
    DISTANCE_BEACH = State()
    PRICE_RANGE = State()
    ATTACH_PHOTOS = State()
    PHOTO_DESCRIPTION = State()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    start_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Бизнес аккаунт", callback_data="business"),
        InlineKeyboardButton("Пример заполнения", callback_data="example")
    )
    await message.answer("Привет! Выберите тип аккаунта для регистрации.", reply_markup=start_markup)
    await Registration.ACCOUNT_TYPE.set()


@dp.callback_query_handler(text="example", state="*")
async def show_example(callback_query: types.CallbackQuery):
    example_text = (
        "Пример заполнения:\n"
        "1. Регион и город: Бишкек, Кыргызстан\n"
        "2. Тип размещения: Гостиница\n"
        "3. Количество мест: 10\n"
        "4. Удобства и тип питания: Wi-Fi, Завтрак, Парковка\n"
        "5. Расстояние до пляжа: 200 м\n"
        "6. Ценовой диапазон: 1500 - 3000 KGS\n"
        "7. Фото и описание: (загрузите фото и добавьте описание)"
    )
    await bot.send_message(callback_query.from_user.id, example_text)

    regions_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Бишкек", callback_data="region_bishkek"),
        InlineKeyboardButton("Ош", callback_data="region_osh")
        # Добавьте больше кнопок для других регионов
    )
    await bot.send_message(callback_query.from_user.id, "Выберите регион:", reply_markup=regions_markup)
    await BusinessRegistration.REGION.set()


@dp.callback_query_handler(state=BusinessRegistration.REGION)
async def choose_region(callback_query: types.CallbackQuery, state: FSMContext):
    region = callback_query.data.split('_')[1]
    await state.update_data(region=region)

    cities_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Город 1", callback_data="city_1"),
        InlineKeyboardButton("Город 2", callback_data="city_2")
        # Добавьте больше кнопок для других городов
    )
    await bot.send_message(callback_query.from_user.id, "Выберите город:", reply_markup=cities_markup)
    await BusinessRegistration.CITY.set()


@dp.callback_query_handler(state=BusinessRegistration.CITY)
async def choose_city(callback_query: types.CallbackQuery, state: FSMContext):
    city = callback_query.data.split('_')[1]
    await state.update_data(city=city)

    await bot.send_message(callback_query.from_user.id, "Теперь выберите тип размещения.")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Гостиница", callback_data="Гостиница"))
    markup.add(InlineKeyboardButton("Гостевой дом", callback_data="Гостевой дом"))
    markup.add(InlineKeyboardButton("Пансионат", callback_data="Пансионат"))
    await bot.send_message(callback_query.from_user.id, "Теперь выберите тип размещения:", reply_markup=markup)
    await BusinessRegistration.ACCOMMODATION_TYPE.set()


@dp.callback_query_handler(state=BusinessRegistration.ACCOMMODATION_TYPE)
async def choose_accommodation_type(callback_query: types.CallbackQuery, state: FSMContext):
    accommodation_type = callback_query.data
    await state.update_data(accommodation_type=accommodation_type)
    await BusinessRegistration.ROOMS_COUNT.set()
    await bot.send_message(callback_query.from_user.id, "Спасибо! Укажите количество мест.")


@dp.message_handler(state=BusinessRegistration.ROOMS_COUNT)
async def choose_rooms_count(message: types.Message, state: FSMContext):
    rooms_count = message.text
    await state.update_data(rooms_count=rooms_count)

    amenities_markup = InlineKeyboardMarkup(row_width=2)
    amenities = ["Wi-Fi", "Завтрак", "Парковка", "Бассейн", "Сауна", "Тренажерный зал"]
    for amenity in amenities:
        amenities_markup.insert(InlineKeyboardButton(amenity, callback_data=f"amenity_{amenity}"))

    await BusinessRegistration.AMENITIES_NUTRITION.set()
    await message.answer("Отлично! Выберите все удобства и тип питания:", reply_markup=amenities_markup)


@dp.callback_query_handler(state=BusinessRegistration.AMENITIES_NUTRITION)
async def add_amenities_nutrition(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amenities = data.get('amenities', [])
    amenity = callback_query.data.split('_')[1]
    if amenity not in amenities:
                amenities.append(amenity)
                await state.update_data(amenities=amenities)
                await callback_query.answer(f"Удобство '{amenity}' добавлено.", show_alert=False)

    if len(amenities) >= 3:  # Ожидаем как минимум 3 удобства
        await BusinessRegistration.DISTANCE_BEACH.set()
        await bot.send_message(callback_query.from_user.id, "Введите расстояние от отеля до пляжа.")
    else:
        await callback_query.answer(f"Удобство '{amenity}' добавлено. Выберите следующее удобство.", show_alert=False)


@dp.message_handler(state=BusinessRegistration.DISTANCE_BEACH)
async def choose_distance_beach(message: types.Message, state: FSMContext):
    distance_beach = message.text
    await state.update_data(distance_beach=distance_beach)
    await BusinessRegistration.PRICE_RANGE.set()
    await message.answer("Укажите ценовой диапазон.")


@dp.message_handler(state=BusinessRegistration.PRICE_RANGE)
async def choose_price_range(message: types.Message, state: FSMContext):
    price_range = message.text
    await state.update_data(price_range=price_range)
    await BusinessRegistration.ATTACH_PHOTOS.set()
    await message.answer("Прикрепите примеры фото вашего отеля (не менее 5 и не более 10).")


@dp.message_handler(content_types=types.ContentType.PHOTO, state=BusinessRegistration.ATTACH_PHOTOS)
async def attach_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    photo_id = message.photo[-1].file_id
    photos.append(photo_id)
    await state.update_data(photos=photos)

    if len(photos) >= 5:
        await message.answer("Введите описание для этого фото.")
        await BusinessRegistration.PHOTO_DESCRIPTION.set()
    else:
        await message.answer(f"Фото добавлено. Добавьте ещё фото. Всего фото: {len(photos)}")


@dp.message_handler(state=BusinessRegistration.PHOTO_DESCRIPTION)
async def add_photo_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    descriptions = data.get('photo_descriptions', [])

    descriptions.append(message.text)
    await state.update_data(photo_descriptions=descriptions)

    if len(photos) < 10:
        await BusinessRegistration.ATTACH_PHOTOS.set()
        await message.answer("Фото и описание добавлены. Прикрепите следующее фото.")
    else:
        await finish_registration(message, state)


async def finish_registration(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await state.finish()
    await message.answer("Спасибо за предоставление информации. Ваш отель успешно зарегистрирован.")


@dp.message_handler(commands=['profile'])
async def view_profile(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if user_data:
        region_city = f"{user_data.get('region')}, {user_data.get('city')}"
        accommodation_type = user_data.get('accommodation_type')
        rooms_count = user_data.get('rooms_count')
        amenities = ", ".join(user_data.get('amenities', []))
        distance_beach = user_data.get('distance_beach')
        price_range = user_data.get('price_range')
        photos = user_data.get('photos', [])
        descriptions = user_data.get('photo_descriptions', [])

        profile_message = (
            f"Регион и город: {region_city}\n"
            f"Тип размещения: {accommodation_type}\n"
            f"Количество мест: {rooms_count}\n"
            f"Удобства: {amenities}\n"
            f"Расстояние до пляжа: {distance_beach}\n"
            f"Ценовой диапазон: {price_range}\n"
            f"Фотографии и описания:\n"
        )

        await message.answer(profile_message)
        for photo, description in zip(photos, descriptions):
            await bot.send_photo(message.chat.id, photo, caption=description)
    else:
        await message.answer("Ваш профиль пока пуст.")


@dp.message_handler(commands=['add_hotel'])
async def add_hotel(message: types.Message):
    await message.answer("Начнем регистрацию нового отеля. Введите регион:")
    await BusinessRegistration.REGION.set()


async def view_all_updates(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()
    updates = user_data.get('updates', [])

    if updates:
        updates_text = "\n".join(updates)
        await message.answer(f"Ваши обновления:\n{updates_text}")
    else:
        await message.answer("У вас пока нет обновлений.")


async def manage_updates(message: types.Message, state: FSMContext):
    await message.answer("Выберите действие по управлению обновлениями:", reply_markup=update_management_markup)


update_management_markup = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Добавить обновление", callback_data="add_update"),
    InlineKeyboardButton("Удалить обновление", callback_data="delete_update"),
    InlineKeyboardButton("Изменить обновление", callback_data="edit_update")
)


@dp.message_handler(commands=['all_updates'])
async def view_all_updates_command(message: types.Message):
    await view_all_updates(message, dp.current_state())


@dp.message_handler(commands=['manage_updates'])
async def manage_updates_command(message: types.Message):
    await manage_updates(message, dp.current_state())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

       
