# qwen-cline

> Integrate [qwen-api](https://github.com/arosyihuddin/qwen-api) with the Cline Extension.

---

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/arosyihuddin/qwen-cline.git
   cd qwen-cline

   ```

2. **Choose an installation method**

   - **Poetry**

     ```bash
     poetry install
     poetry shell
     ```

   - **venv**

     ```bash
     python3.12 -m venv .venv
     # macOS/Linux
     source .venv/bin/activate
     # Windows PowerShell
     .\.venv\Scripts\activate

     pip install --upgrade pip
     pip install -r requirements.txt
     ```

---

## ⚙️ Configuration

Create a `.env` file at the project root:

```ini
QWEN_AUTH_TOKEN=<your_auth_token>
QWEN_COOKIE=<your_cookie>
```

> **Note:** Follow the authentication guide in the [qwen-api repository](https://github.com/arosyihuddin/qwen-api) to obtain your token and cookie.

---

## ▶️ Running the Server

The server will run at `http://localhost:8000` and expose these endpoints:

- **GET** `/v1/models`
- **POST** `/v1/chat/completions` (streaming via SSE)

```bash
# With Poetry
poetry run uvicorn qwen_cline.server:app --host 0.0.0.0 --port 8000

# With venv
uvicorn qwen_cline.server:app --host 0.0.0.0 --port 8000
```

---

## 🧪 Verification

1. **List available models**

   ```bash
   curl http://localhost:8000/v1/models
   ```

2. **Test streaming chat**

   ```bash
   curl -N -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "qwen3-235b-a22b",
       "messages": [{"role":"user","content":"Hello, Qwen!"}],
       "stream": true
     }'
   ```

---

## 🔗 Integration with Cline (LM Studio Agent)

1. Open the **Cline** sidebar in VS Code and select **LM Studio** as the provider.
2. **Use Custom Base URL**.
3. Enter:

   ```text
   http://localhost:8000
   ```

4. Cline will automatically call `GET /v1/models` and detect the model `qwen3-235b-a22b`.
5. Choose the model, save

Now, Cline will use your `qwen-cline` server as its AI backend, streaming tokens in real time within your IDE! 🎉
