from workbench.doctor import OPTIONAL_MODULES, REQUIRED_MODULES, TOOLS, inspect_environment


def test_environment_report_has_required_and_optional_dependencies():
    report = inspect_environment()
    assert set(report["required_packages"]) == set(REQUIRED_MODULES)
    assert set(report["optional_packages"]) == set(OPTIONAL_MODULES)
    assert set(report["commands"]) == set(TOOLS)
    assert isinstance(report["python_supported"], bool)
    assert isinstance(report["missing_required"], list)


def test_missing_optional_tools_do_not_become_required_dependencies():
    report = inspect_environment()
    assert "node" not in report["missing_required"]
    assert "git" not in report["missing_required"]
    assert "ssh" not in report["missing_required"]
