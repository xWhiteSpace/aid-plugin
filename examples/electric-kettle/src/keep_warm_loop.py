# @trace UNT-KTL-004
def keep_warm_pulse(water_temp_c, keep_warm_on, elapsed_s):
    if not keep_warm_on:
        return False, False
    if elapsed_s >= 1800:
        return False, False
    if water_temp_c < 75:
        return True, True
    if water_temp_c >= 85:
        return False, True
    return None, True
