## How to run


1. Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `config.json`.  
   To obtain your `api_id` and `api_hash`:
   - Go to [my.telegram.org](https://my.telegram.org/auth) and log in with the phone number of your developer account.
   - Click on **API Development tools**.
   - Click **Create new application** and fill in the fields (App title and Short name).
   - Click **Create application**.
   - You will receive your `api_id` and `api_hash`.  
     ⚠️ **Important:** Your `api_hash` is secret. Do not share it or publish it anywhere.

3. Run:
   ```bash
   python main.py
   ```
