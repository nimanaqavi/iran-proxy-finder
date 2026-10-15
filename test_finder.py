from finder import extract_ips

def test_extract_ips_valid():
    assert extract_ips("192.168.1.1") == {"192.168.1.1"}
    assert extract_ips("some text 8.8.8.8 here") == {"8.8.8.8"}
    assert extract_ips("1.1.1.1 and 8.8.4.4") == {"1.1.1.1", "8.8.4.4"}
    assert extract_ips("Duplicates: 1.1.1.1, 1.1.1.1") == {"1.1.1.1"}

def test_extract_ips_invalid():
    assert extract_ips("256.256.256.256") == set()
    assert extract_ips("999.1.1.1") == set()
    assert extract_ips("192.168.1") == set()
    assert extract_ips("just some text") == set()
    assert extract_ips("") == set()
