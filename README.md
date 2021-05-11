# Notion Control

> You need to create `.secrets.toml` and `degiro/config.json` file

```
# .secrets.toml (example)

token="8c9d6348569bc29463209e0e21d..."
stocks_site="https://www.notion.so/1ff359..."

# degiro/config.json (example)

{
"username" : "degiro_username",
"password" : "degiro_password"
}
```

## Install

```
# Linux

python3 -m venv .env
source .env/bin/activate
pip install --upgrade pip
pip install -r requirements.notion.txt
pip install -r requirements.txt

# Windows

```

## Run

```
# Under virtual environment

python main.py
```

## How to get Notion token

- Chrome, visit site
- Network - Cache
- Token thingie
