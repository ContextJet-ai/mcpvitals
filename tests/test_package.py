def test_version_exposed():
    import mcpvitals
    assert isinstance(mcpvitals.__version__, str)
    assert mcpvitals.__version__
