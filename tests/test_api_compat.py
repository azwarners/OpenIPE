def test_root_api_create_app_remains_supported_composition_entrypoint():
    from openipe.api.REST.app import create_app as rest_create_app
    from openipe.api.app import create_app

    assert callable(create_app)
    assert callable(rest_create_app)
    assert create_app is not rest_create_app
