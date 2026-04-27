import asyncio, random
from aiogram import Router, F
from aiogram.types import Message
from database.db import update_balance, get_user
from utils.formatters import fmt

router = Router()
active_bets = {}

