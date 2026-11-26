import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("talvimeri", pathlib.Path(__file__).parents[1] / "tools" / "talvimeri.py")
tm = importlib.util.module_from_spec(spec); spec.loader.exec_module(tm)

def test_merialue():
    assert tm.merialue(60.15, 24.95) == "Suomenlahti"   # Helsinki
    assert tm.merialue(60.55, 27.10) == "Suomenlahti"   # Hamina
    assert tm.merialue(60.43, 22.22) == "Saaristomeri"  # Turku
    assert tm.merialue(61.13, 21.46) == "Selkämeri"     # Rauma
    assert tm.merialue(65.00, 25.40) == "Perämeri"      # Oulu

def test_p90():
    assert tm.p90([1.0] * 9) is None
    assert tm.p90([float(i) for i in range(1, 11)]) == 9.0
