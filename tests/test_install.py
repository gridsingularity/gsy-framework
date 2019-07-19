
from d3a_interface import interface


def test_install():
    assert interface.test_interface() == "d3a-interface was successfully installed and imported"
