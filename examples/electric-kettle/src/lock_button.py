# @trace UNT-KTL-005
def on_lock_hold(lock_hold_ms, locked):
    if lock_hold_ms >= 3000:
        return not locked
    return locked
