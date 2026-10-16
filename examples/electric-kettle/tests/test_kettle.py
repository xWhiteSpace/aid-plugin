from boil_detector import on_temp_sample
from dry_guard import on_element_temp
from keep_warm_loop import keep_warm_pulse
from lock_button import on_lock_hold
from start_guard import heater_should_run


# @trace TST-KTL-001
def test_acceptance_boil_water():
    assert heater_should_run(True, True, False, True) is True


# @trace TST-KTL-002
def test_acceptance_auto_shut_off_at_boil():
    action, state = on_temp_sample(100.0)
    assert action == "heater_off"
    assert state == "idle"


# @trace TST-KTL-003
def test_acceptance_boil_dry_protection():
    heater, fault = on_element_temp(140.1, False)
    assert heater is False
    assert fault is True


# @trace TST-KTL-004
def test_acceptance_keep_warm():
    pulse, stay = keep_warm_pulse(80.0, True, 0)
    assert pulse is None
    assert stay is True
    pulse, stay = keep_warm_pulse(80.0, True, 1800)
    assert pulse is False
    assert stay is False


# @trace TST-KTL-005
def test_acceptance_child_lock():
    assert heater_should_run(True, True, True, True) is False


# @trace TST-KTL-006
def test_start_refused_off_base():
    assert heater_should_run(True, False, False, True) is False


# @trace TST-KTL-007
def test_panel_command_round_trip():
    assert on_lock_hold(3000, False) is True


# @trace TST-KTL-008
def test_boil_detector_boundary():
    action, state = on_temp_sample(99.9)
    assert action is None
    assert state is None
    action, state = on_temp_sample(100.0)
    assert action == "heater_off"
    assert state == "idle"


# @trace TST-KTL-009
def test_dry_guard_boundary():
    heater, fault = on_element_temp(140, False)
    assert heater is None
    assert fault is False
    heater, fault = on_element_temp(140.1, False)
    assert heater is False
    assert fault is True


# @trace TST-KTL-010
def test_keep_warm_loop_band_and_timeout():
    pulse, stay = keep_warm_pulse(74.9, True, 0)
    assert pulse is True
    assert stay is True
    pulse, stay = keep_warm_pulse(85, True, 0)
    assert pulse is False
    assert stay is True
    pulse, stay = keep_warm_pulse(80, True, 1800)
    assert pulse is False
    assert stay is False


# @trace TST-KTL-011
def test_lock_button_hold():
    assert on_lock_hold(2999, False) is False
    assert on_lock_hold(3000, False) is True


# @trace TST-KTL-012
def test_start_guard_truth_table():
    assert heater_should_run(True, True, True, True) is False
