import pytest
import numpy
import netCDF4
import exodus as exo

# Disables all warnings in this module
pytestmark = pytest.mark.filterwarnings('ignore')

def test_open():
    # Test that we can open a file without any errors
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    assert exofile.data
    exofile.close()


def test_create(tmpdir):
    # Test that we can create a file without any errors
    exofile = exo.Exodus(tmpdir + '/test.ex2', 'w')
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
        exofile = exo.Exodus(tmpdir + '/test.ex2', 'w', True, "NOTAFORMAT")
    with pytest.raises(PermissionError):
        exofile = exo.Exodus(tmp_path, 'w', True)
    with pytest.raises(ValueError):
        exofile = exo.Exodus(tmpdir + '/test2.ex2', 'w', True, "NETCDF4", 7)


def test_float(tmpdir):
    exofile = exo.Exodus(tmpdir + '/test.ex2', 'w', word_size=4)
    assert type(exofile.to_float(1.2)) == numpy.single
    exofile = exo.Exodus(tmpdir + '/test2.ex2', 'w', word_size=8)
    assert type(exofile.to_float(1.2)) == numpy.double
    exofile.close()


def test_parameters():
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    assert exofile.parameters
    assert exofile.title
    assert exofile.version
    assert exofile.api_version
    assert exofile.word_size
    exofile.close()

def test_get_nodeset():
    # Testing that get_nodeset returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 6 nodesets with 81 nodes and 1 nodeset with 729 nodes
    exofile = exo.Exodus('sample-files/cube_1ts_mod.e', 'r')
    i = 1
    while i <= 6:
        nodeset = exofile.get_nodeset(i)
        assert len(nodeset) == 81
        i += 1
    assert len(exofile.get_nodeset(7)) == 729
    exofile.close()
    # Nodeset 1 in 'disk_out_ref.ex2' has 1 node with ID 7210
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    nodeset = exofile.get_nodeset(1)
    assert nodeset[0] == 7210
    exofile.close()