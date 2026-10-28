# Task 1 Brief: Environment and Dependencies Setup

## Files
- Create: `requirements.txt`
- Create: `tests/conftest.py`
- Test: `tests/test_env.py`

## Instructions
1. Create `requirements.txt`:
```text
PySide6>=6.5.0
onnxruntime>=1.15.0
numpy>=1.24.0
pytest>=7.0.0
```
2. Create `tests/conftest.py` to ensure project root is on `sys.path`.
3. Create `tests/test_env.py` verifying imports and checking if ffmpeg executable exists via `shutil.which("ffmpeg")`.
4. Report status.
