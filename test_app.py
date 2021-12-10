from os import path


def test_necessary_files_API():
    assert path.exists("./API_Polygon/API_polygon.py")


def test_necessary_files_lambda1():
    assert path.exists("./lambda1/lambda_function.py")
    assert path.exists("./lambda1/lambda1_local.py")
    assert path.exists("./lambda1/load_history.py")


def test_necessary_files_lambda2():
    assert path.exists("./lambda2_docker/Dockerfile")
    assert path.exists("./lambda2_docker/lambda_function.py")
