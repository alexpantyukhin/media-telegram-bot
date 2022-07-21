from typing import List, Any, Awaitable, Dict, Callable
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
import logging
import settings
import os
import shutil
from datetime import datetime

PHOTOS = 'photos'
VIDEOS = 'videos'
ISO_FORMAT_DATE = "%Y-%m-%dT%H:%M:%S.%f"
EXPECTING = 'expecting'

logging.basicConfig(filename=os.path.join(settings.LOG_FILE_PATH, 'log.txt'),
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessMiddleware(BaseMiddleware):
    def __init__(self, allowed_access_ids: List[int]):
        self.allowed_access_ids_set = set(allowed_access_ids)
        super().__init__()

    async def on_process_message(self, message: types.Message, _):
        if message.from_user.id not in self.allowed_access_ids_set:
            await message.answer("Access Denied")
            logger.warning(f'Someone tries to access the bot with id: {message.from_user.id}')
            raise CancelHandler()

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:

        try:
            return await handler(event, data)

        except Exception:
            logger.error("Exception during the handle request.", exc_info=True)
            raise


storage = MemoryStorage()
bot = Bot(token=settings.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=storage)
allowed_access_ids = list(map(lambda x: int(x.strip()), settings.ALLOWED_ACCESS_IDS.split(',')))
dp.middleware.setup(AccessMiddleware(allowed_access_ids))

class States(StatesGroup):
    expect_folder = State()

def get_buffer_path(user_id: int) -> str:
    return os.path.join(settings.BUFFER_PATH, f'{user_id}_temp')

async def handle_docs(message: types.Message,
                      state: FSMContext):

    # Check if the bot sent the request about the destination folder for media
    async with state.proxy() as data:
        utc_now = datetime.utcnow()
        if EXPECTING in data and \
            (utc_now - datetime.strptime(data[EXPECTING], ISO_FORMAT_DATE)).total_seconds() <= settings.EXPECT_SETTINGS:
            return

        data[EXPECTING] = utc_now.isoformat()

    # Send the request for select the destination folder
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True)
    for directory in os.listdir(settings.DESTINATION_PATH):
        keyboard = keyboard.add(KeyboardButton(directory))

    await message.answer('Select folder to upload pics.', reply_markup=keyboard)
    await States.expect_folder.set()


@dp.message_handler(content_types=['photo'])
async def handle_docs_photo(message: types.Message, state: FSMContext):
    date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    buffer_path = os.path.join(get_buffer_path(message.from_user.id), f'image_{date_time_str}.jpg')

    await message.photo[-1].download(destination_file=buffer_path, make_dirs=True)
    await handle_docs(message, state)


@dp.message_handler(content_types=['video'])
async def handle_docs_video(message: types.Message, state: FSMContext):
    date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    buffer_path = os.path.join(get_buffer_path(message.from_user.id), f'video_{date_time_str}.mp4')

    file_id = message.video.file_id
    file = await bot.get_file(file_id)

    await file.download(destination_file=buffer_path, make_dirs=True)
    await message.answer('video file is uploaded')
    await handle_docs(message, state)


@dp.message_handler(state=States.expect_folder)
async def save_to_folder(message: types.Message, state: FSMContext):
    buffer_path = get_buffer_path(message.from_user.id)

    allfiles = os.listdir(buffer_path)
    destination_folder = os.path.join(settings.DESTINATION_PATH, message.text)

    for f in allfiles:
        shutil.move(os.path.join(buffer_path, f), os.path.join(destination_folder, f))

    await message.answer(f'{len(allfiles)} files are saved into "{message.text}" folder.')
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
