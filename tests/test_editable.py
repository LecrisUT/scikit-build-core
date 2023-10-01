import shutil

import pytest
from conftest import PackageInfo, VEnv, process_package


@pytest.mark.compile()
@pytest.mark.configure()
@pytest.mark.integration()
@pytest.mark.parametrize("isolate", [True, False])
@pytest.mark.usefixtures("navigate_editable")
def test_navigate_editable(isolated, isolate):
    isolate_args = ["--no-build-isolation"] if not isolate else []
    isolated.install("pip>=23")
    if not isolate:
        isolated.install("scikit-build-core[pyproject]")

    isolated.install(
        "-v", "--config-settings=build-dir=build/{wheel_tag}", *isolate_args, "-e", "."
    )

    value = isolated.execute("import shared_pkg; shared_pkg.call_c_method()")
    assert value == "c_method"

    value = isolated.execute("import shared_pkg; shared_pkg.call_py_method()")
    assert value == "py_method"

    value = isolated.execute("import shared_pkg; shared_pkg.read_py_data_txt()")
    assert value == "Some_value_Py"

    value = isolated.execute("import shared_pkg; shared_pkg.read_c_generated_txt()")
    assert value == "Some_value_C"


@pytest.mark.compile()
@pytest.mark.configure()
@pytest.mark.integration()
@pytest.mark.parametrize("editable", [True, False])
def test_cython_pxd(monkeypatch, tmp_path, editable):
    env_path = tmp_path / "env"
    env = VEnv(env_path)
    editable_flag = ["-e"] if editable else []

    try:
        package1 = PackageInfo(
            "cython_pxd_editable/pkg1",
        )
        tmp_path1 = tmp_path / "pkg1"
        tmp_path1.mkdir()
        process_package(package1, tmp_path1, monkeypatch)

        env.install("pip>=23")
        env.install("cython")
        env.install("scikit-build-core[pyproject]")

        # This succeeds
        env.install(
            "-v", "--config-settings=build-dir=build/{wheel_tag}", *editable_flag, "."
        )

        # This fails
        env.install(
            "-v",
            "--config-settings=build-dir=build/{wheel_tag}",
            "--no-build-isolation",
            *editable_flag,
            ".",
        )

        # package2 = PackageInfo(
        #     "cython_pxd_editable/pkg2",
        # )
        # tmp_path2 = tmp_path / "pkg2"
        # tmp_path2.mkdir()
        # process_package(package2, tmp_path2, monkeypatch)
        #
        # env.install("pip>=23")
        # env.install("cython")
        # env.install("scikit-build-core[pyproject]")
        #
        # env.install(
        #     "-v", "--config-settings=build-dir=build/{wheel_tag}", "--no-build-isolation", *editable_flag, "."
        # )
    finally:
        shutil.rmtree(env_path, ignore_errors=True)
