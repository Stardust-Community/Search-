# ============================================================
#   ꜱᴛᴀᴛᴇ — multi-step conversation state per admin
# ============================================================

# Structure:
#   _state[user_id] = {
#       "step": str,          # current step name
#       "data": dict,         # accumulated data
#   }

_state: dict = {}

STEPS = {
    # Post creation flow
    "AWAIT_POST_NAME":   "AWAIT_POST_NAME",
    "AWAIT_POST_IMAGE":  "AWAIT_POST_IMAGE",
    "AWAIT_POST_LINK":   "AWAIT_POST_LINK",

    # Auto-delete flow
    "AWAIT_AD_DM_TIME":  "AWAIT_AD_DM_TIME",
    "AWAIT_AD_CH_TIME":  "AWAIT_AD_CH_TIME",
}


def set_state(user_id: int, step: str, **data):
    _state[user_id] = {"step": step, "data": data}

def get_state(user_id: int) -> dict | None:
    return _state.get(user_id)

def clear_state(user_id: int):
    _state.pop(user_id, None)

def get_step(user_id: int) -> str | None:
    s = _state.get(user_id)
    return s["step"] if s else None

def update_data(user_id: int, **kwargs):
    if user_id in _state:
        _state[user_id]["data"].update(kwargs)

def get_data(user_id: int) -> dict:
    s = _state.get(user_id)
    return s["data"] if s else {}
