# @trace UNT-KTL-003
def on_element_temp(element_temp_c, fault):
    if element_temp_c > 140:
        return False, True
    return None, fault
