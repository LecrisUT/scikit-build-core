import shutil
import sys
import tarfile
import textwrap
import zipfile
from pathlib import Path

import pytest

from scikit_build_core.setuptools.build_meta import build_sdist, build_wheel

pytestmark = pytest.mark.setuptools

DIR = Path(__file__).parent.resolve()
HELLO_PEP518 = DIR / "packages/simple_setuptools_ext"


def test_pep517_sdist(tmp_path, monkeypatch):
    correct_metadata = textwrap.dedent(
        """\
        Metadata-Version: 2.1
        Name: cmake-example
        Version: 0.0.1
        Requires-Python: >=3.7
        Provides-Extra: test
        """
        # TODO: why is this missing?
        # Requires-Dist: pytest>=6.0; extra == "test"
    )
    metadata_set = set(correct_metadata.strip().splitlines())

    dist = tmp_path / "dist"
    dist.mkdir()

    # create a temporary copy of the package source so we don't contaminate the
    # main source tree with build artefacts
    src = tmp_path / "src"
    shutil.copytree(HELLO_PEP518, src)
    monkeypatch.chdir(src)

    if Path("dist").is_dir():
        shutil.rmtree("dist")

    out = build_sdist(str(dist))

    (sdist,) = dist.iterdir()
    assert sdist.name == "cmake-example-0.0.1.tar.gz"
    assert sdist == dist / out

    with tarfile.open(sdist) as f:
        file_names = set(f.getnames())
        assert file_names == {
            f"cmake-example-0.0.1/{x}"
            for x in (
                # TODO: "CMakeLists.txt",
                "PKG-INFO",
                "cmake_example.egg-info",
                "cmake_example.egg-info/PKG-INFO",
                "cmake_example.egg-info/SOURCES.txt",
                "cmake_example.egg-info/dependency_links.txt",
                "cmake_example.egg-info/not-zip-safe",
                "cmake_example.egg-info/requires.txt",
                "cmake_example.egg-info/top_level.txt",
                "pyproject.toml",
                "setup.cfg",
                "setup.py",
                # TODO: "src/main.cpp",
            )
        } | {"cmake-example-0.0.1"}
        pkg_info = f.extractfile("cmake-example-0.0.1/PKG-INFO")
        assert pkg_info
        pkg_info_contents = set(pkg_info.read().decode().strip().splitlines())
        assert metadata_set <= pkg_info_contents


@pytest.mark.compile()
@pytest.mark.configure()
@pytest.mark.skipif(
    sys.platform.startswith("cygwin"), reason="Cygwin fails here with ld errors"
)
def test_pep517_wheel(tmp_path, monkeypatch, virtualenv):
    dist = tmp_path / "dist"
    dist.mkdir()

    # create a temporary copy of the package source so we don't contaminate the
    # main source tree with build artefacts
    src = tmp_path / "src"
    shutil.copytree(HELLO_PEP518, src)
    monkeypatch.chdir(src)

    if Path("dist").is_dir():
        shutil.rmtree("dist")
    out = build_wheel(str(dist))
    (wheel,) = dist.glob("cmake_example-0.0.1-*.whl")
    assert wheel == dist / out

    if sys.version_info >= (3, 8):
        with wheel.open("rb") as f:
            p = zipfile.Path(f)
            file_names = [p.name for p in p.iterdir()]

        assert len(file_names) == 2
        assert "cmake_example-0.0.1.dist-info" in file_names
        file_names.remove("cmake_example-0.0.1.dist-info")
        (so_file,) = file_names

        assert so_file.startswith("cmake_example")
        print("SOFILE:", so_file)

    virtualenv.install(wheel)

    version = virtualenv.execute(
        "import cmake_example; print(cmake_example.__version__)"
    )
    assert version.strip() == "0.0.1"

    add = virtualenv.execute("import cmake_example; print(cmake_example.add(1, 2))")
    assert add.strip() == "3"
