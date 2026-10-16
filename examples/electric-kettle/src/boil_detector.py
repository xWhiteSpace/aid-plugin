# @trace UNT-KTL-002
def on_temp_sample(water_temp_c):
    if water_temp_c >= 100:
        return "heater_off", "idle"
    return None, None
