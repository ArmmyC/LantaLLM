# Swap Models With vLLM

The generic scripts in `lanta/scripts/` let you download and serve another Hugging Face model without editing files.

Remote project root:

```bash
/project/zz992000-zdevb/zz992005/ub127/SiliconCraft
```

## 1. Download A Model

Example:

```bash
cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
MODEL_REPO=Qwen/Qwen3.6-35B-A3B bash scripts/download-model.sh
```

Another model:

```bash
MODEL_REPO=meta-llama/Llama-3.1-8B-Instruct bash scripts/download-model.sh
```

Optional custom folder name:

```bash
MODEL_REPO=org/model-name MODEL_NAME=my-test-model bash scripts/download-model.sh
```

## 2. Serve The Model

```bash
MODEL_REPO=Qwen/Qwen3.6-35B-A3B \
SERVED_MODEL_NAME=qwen36 \
TP=4 \
MAX_MODEL_LEN=131072 \
REASONING_PARSER=qwen3 \
bash scripts/submit-model.sh
```

For a smaller non-Qwen model:

```bash
MODEL_REPO=meta-llama/Llama-3.1-8B-Instruct \
SERVED_MODEL_NAME=llama31-8b \
TP=1 \
MAX_MODEL_LEN=32768 \
bash scripts/submit-model.sh
```

Only one model is served by a vLLM job at a time. To swap models, cancel the running job and submit a new one.

## 3. Test The Running Model

```bash
MODEL_REPO=Qwen/Qwen3.6-35B-A3B \
SERVED_MODEL_NAME=qwen36 \
bash scripts/test-model-api.sh
```

## 4. Use From Local CLI

Set the model name your vLLM job serves:

```powershell
$env:MODEL="qwen36"
.\cli\qwen-chat.ps1 "Hello"
```

For public Funnel sharing, friends should use the same served model name in their requests.

## Notes

- `MODEL_REPO` is the Hugging Face repo id.
- `MODEL_NAME` is the local folder under `models/`; default is the last part of `MODEL_REPO`.
- `SERVED_MODEL_NAME` is the API model name clients use.
- `TP` should match how many GPUs you want for tensor parallelism.
- `MAX_MODEL_LEN` should be reduced for larger models if you hit memory pressure.
- `REASONING_PARSER=qwen3` is Qwen-specific; leave it unset for ordinary models.
