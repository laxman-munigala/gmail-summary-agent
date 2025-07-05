import json,yaml,os
from dotenv import load_dotenv, find_dotenv


def load_config(config_file="config.yaml"):
  with open(config_file, 'r') as file:
    config = yaml.safe_load(file)
  return config

load_dotenv("./private_config/.env")

app_config = load_config()
print(f"Loaded configuration: {json.dumps(app_config, indent=2)}")

def get_model():
    return app_config['lite_llm'].get('model', 'openrouter/deepseek/deepseek-chat-v3-0324')

def get_max_input_chars():
    return app_config['lite_llm'].get('max_input_chars', 1000000)

def get_max_output_tokens():
    return app_config['lite_llm'].get('max_output_tokens', 1000000)

def get_gmail_max_results():
    return app_config['gmail'].get('max_results', 10)

def get_gmail_query():
    return app_config['gmail'].get('query', "newer_than:1d AND category:UPDATES")

def get_gmail_credential_folder():
    return os.getenv("GMAIL_CREDENTIALS_FOLDER", "./private_config/")

def get_prompt_template():
    return app_config['lite_llm'].get('prompt_template', "")

def get_gmail_categories():
    categories = app_config['gmail'].get('categories', [])
    if not categories:
        print("No Gmail categories found in configuration. Defaulting to ['PRIMARY', 'UPDATES', 'SOCIAL', 'PROMOTIONS', 'FORUMS'].")
        return ["PRIMARY", "UPDATES", "SOCIAL", "PROMOTIONS", "FORUMS"]
    return categories