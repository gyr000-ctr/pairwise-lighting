import math

import pytest

import lightkit

def _raises(fn, exc=ValueError):
    try:
        fn()
    except exc:
        return True
    return False

def _l():
    return lightkit.Light((0.0, 0.0), 10.0)


def _check_light_at_center():
    return abs(_l().attenuation((0.0, 0.0)) - 1.0) < 1e-9


def _check_light_at_edge():
    return abs(_l().attenuation((10.0, 0.0))) < 1e-9


def _check_light_outside():
    return _l().attenuation((100.0, 0.0)) == 0.0


def _check_light_monotonic():
    l = _l()
    return l.attenuation((1.0, 0.0)) >= l.attenuation((5.0, 0.0))


def _check_light_combine():
    return abs(lightkit.Light.combine([_l()], (0.0, 0.0)) - 1.0) < 1e-9


def _check_light_combine_empty():
    return lightkit.Light.combine([], (0.0, 0.0)) == 0.0


def _check_light_bad_radius():
    return _raises(lambda: lightkit.Light((0.0, 0.0), 0.0))


def _check_light_radius_zero():
    return _raises(lambda: lightkit.Light((0.0, 0.0), -1.0))


def _check_light_negative_pos():
    l = lightkit.Light((-5.0, 0.0), 10.0)
    return abs(l.attenuation((-5.0, 0.0)) - 1.0) < 1e-9


def _check_light_det():
    return _l().attenuation((3.0, 0.0)) == _l().attenuation((3.0, 0.0))


def _check_light_type():
    return isinstance(_l().attenuation((1.0, 0.0)), float)


def _check_light_range():
    v = _l().attenuation((7.0, 0.0))
    return 0.0 <= v <= 1.0


def _check_light_two():
    a = lightkit.Light((0.0, 0.0), 10.0)
    b = lightkit.Light((10.0, 0.0), 10.0)
    return lightkit.Light.combine([a, b], (5.0, 0.0)) > 0.0


def _check_light_edge_zero():
    return _l().attenuation((9.999, 0.0)) > 0.0


def _check_light_no_mutation():
    l = _l()
    l.attenuation((1.0, 1.0))
    return l.attenuation((0.0, 0.0)) == 1.0

CASES = [("light_at_center", "_check_light_at_center"), ("light_at_edge", "_check_light_at_edge"), ("light_outside", "_check_light_outside"), ("light_monotonic", "_check_light_monotonic"), ("light_combine", "_check_light_combine"), ("light_combine_empty", "_check_light_combine_empty"), ("light_bad_radius", "_check_light_bad_radius"), ("light_radius_zero", "_check_light_radius_zero"), ("light_negative_pos", "_check_light_negative_pos"), ("light_det", "_check_light_det"), ("light_type", "_check_light_type"), ("light_range", "_check_light_range"), ("light_two", "_check_light_two"), ("light_edge_zero", "_check_light_edge_zero"), ("light_no_mutation", "_check_light_no_mutation")]


@pytest.mark.parametrize("name,check", CASES, ids=[c[0] for c in CASES])
def test_spec(name, check):
    assert globals()[check]() is True
