## Run

1) Create env:
cp .env.example .env
# put BOT_TOKEN

2) Install:
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

3) Start:
python -m pigeon_mail_bot.main
