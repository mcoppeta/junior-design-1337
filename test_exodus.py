import pytest
import exodus as exo


def test_open():
    # Test that we can open a file without any errors
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    assert exofile.data
    exofile.close()


def test_create(tmpdir):
    # Test that we can create a file without any errors
    exofile = exo.Exodus(tmpdir + '/test.exo', 'w')
    assert exofile.data
    exofile.close()


def test_exodus_init_exceptions(tmp_path, tmpdir):
    # Test that the Exodus.__init__() errors all work
    with pytest.raises(FileNotFoundError):
        exofile = exo.Exodus('some fake directory/notafile.xxx', 'r')
    with pytest.raises(ValueError):
        exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'z')
    with pytest.raises(OSError):
        exofile = exo.Exodus(tmp_path, 'w', False)
    with pytest.raises(ValueError):
        exofile = exo.Exodus(tmpdir + '/test.exo', 'w', True, "NOTAFORMAT")
    with pytest.raises(PermissionError):
        exofile = exo.Exodus(tmp_path, 'w', True)


