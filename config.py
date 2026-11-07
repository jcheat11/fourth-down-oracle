"""Single place for settings that results depend on (T4, prompt versioning).

Anything that changes Oracle output lives here, so each run-log row can record
exactly which model and prompt produced it.
"""

# T4: pinned explicitly, never a default. Set after running access_check.py
# and picking a Flash or Flash-Lite model from the list.
MODEL_NAME = None  # e.g. "gemini-2.5-flash" -- Josh picks
