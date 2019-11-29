import requests
import pytest

def get_csrf(contents):
    c = contents.index('csrf')
    c = contents.index('value',c)
    c = contents.index('"',c)
    final = contents.index('"',c+1)
    csrf = contents[c+1:final]
    return csrf


def test_register():
    s = requests.Session()
    r = s.get('http://localhost:5000/register')
    a = r.text
    assert 'Register' in r.text
    contents = r.text
    csrf = get_csrf(contents)
    data = {'uname':'a','pword':'p','2fa':'12345','csrf':csrf}
    r = s.post('http://localhost:5000/register',data=data)
    b = r.text
    assert 'success' in r.text
    return s

def test_login():
    s = requests.Session()
    r = s.get('http://localhost:5000/login')
    assert 'Login' in r.text
    csrf = get_csrf(r.text)
    data = {'uname':'a','pword':'p','2fa':'12345','csrf':csrf}
    r = s.post('http://localhost:5000/login',data=data)
    assert 'success' in r.text
    return s

@pytest.fixture
def login():
    s = requests.Session()
    r = s.get('http://localhost:5000/login')
    csrf = get_csrf(r.text)
    data = {'uname':'a','pword':'p','2fa':'12345','csrf':csrf}
    r = s.post('http://localhost:5000/login',data=data)
    assert 'success' in r.text
    return s

def test_spell_check(login):
    r = login.get('http://localhost:5000/spell_check')
    test_text ="foo bar baz this is a real word asdf"
    csrf = get_csrf(r.text)
    data = {'inputtext':test_text, 'csrf':csrf}
    r = login.post('http://localhost:5000/spell_check', data=data)
    assert 'Submitted Words' in r.text
    assert test_text in r.text
    assert 'Misspelled' in r.text
