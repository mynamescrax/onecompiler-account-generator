# OneCompiler Account Generator

Automates OneCompiler signup with temp emails, Turnstile solving, and OTP verification.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Edit `config.py` then run:

```bash
python main.py
```

Output goes to `output/accounts.txt` and `output/tokens.txt`.

## Config

| Key | Default | Description |
|---|---|---|
| `count` | 10 | Number of accounts to create |
| `threads` | 1 | Parallel browser instances |
| `headless` | False | Run browser headless (less reliable) |
| `turnstile_timeout` | 30 | Seconds to wait for Turnstile |
| `otp_timeout` | 90 | Seconds to wait for OTP email |



old and unused now, will not be updated
