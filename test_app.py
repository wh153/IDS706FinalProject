from os import path


def test_necessary_files():
    assert path.exists("./API_Polygon/API_polygon.py")
    assert path.exists("./lambda1/lambda_function.py")
    assert path.exists("./lambda1/lambda1_local.py.py")
    assert path.exists("./lambda1/load_history.py")
