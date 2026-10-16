# @trace UNT-KTL-001
def heater_should_run(start_pressed, on_base, locked, water_present):
    return start_pressed and on_base and (not locked) and water_present
