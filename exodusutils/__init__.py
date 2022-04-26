"""
# Introduction

Python Exodus Utilities is a Python library for interfacing with Exodus II files and assisting in performing some common
tasks. This library's only requirements are Python 3.7 or newer, [numpy](https://numpy.org/), and
[netcdf4-python](https://unidata.github.io/netcdf4-python/).

The primary purpose of this library is to allow uses to easily read and modify Exodus II files without having to go
through a more complicated interface or wrapper library. This library also includes some helpful functions for writing
out a subset of a mesh, determining the difference between two files, merging and splitting sets, and more.

Python Exodus Utilities supports most basic Exodus II features defined in
[SAND92-2137](https://www.osti.gov/servlets/purl/10102115) and the
[new documentation](https://gsjaardema.github.io/seacas-docs/exodusII-new.pdf), but lacks newer and more complicated
features from the [C library](https://gsjaardema.github.io/seacas-docs/sphinx/html/index.html#exodus-library) such as
assembly.

# Tutorial
## Opening and closing an Exodus II file
To open an Exodus II file, create an instance of the `exodusutils.exodus.Exodus` class with the path to the file you
want to open and the mode you want to open it in. Mode 'r' opens the file in read only mode and mode 'a' opens it for
reading and writing.

When you are done working with the Exodus II file, call the `close` function on the `Exodus` object. This both closes
the object itself, meaning you cannot use it anymore, and closes access to the actual file on disk as well.

```
# Open the Exodus II file named "biplane.exo" in read mode located in the
# directory "sample-files" relative to the script's directory
ex = Exodus("sample-files/biplane.exo", 'r')
# Print out the title attribute of the file
print(ex.title)
# ...
# whatever other code you need to run
# ...
# We're done with the file, so close it
ex.close()
```
## Difference between two Exodus II files
To quickly view the difference between two `Exodus` objects you can use the `exodusutils.exodus.Exodus.diff` function.
`diff` quickly prints out the number of certain features in the file. You can also use the more specific
`exodusutils.exodus.Exodus.diff_nodeset` function to print out the differences between a node set in one file and a
node set in another file. If the two Exodus files are similar, these functions will produce meaningful output, but
for two completely different files, the output will likely not be of use.

Of course, if these functions do not provide an ideal level of detail, you can always manually compare the data stored
in two `Exodus` objects.
## Output a subset of an Exodus II file
If you have a big Exodus file and want to work with only a part of the whole mesh, you can use
`exodusutils.output_subset` to output a part of the mesh to a new file.

`output_subset` has many options for selecting which part of the mesh you want to write to a new file. To assist with
selecting parts of each individual block and set, `output_subset` takes in lists of selectors from
`exodusutils.selector`. Each selector corresponds to a single block or set from the input file and allows you to choose
which elements/sides/nodes you want to keep, which variables you want to keep, and which attributes to keep (for element
blocks). `output_subset` also requires one `exodusutils.selector.PropertySelector` to choose which element block,
node set, and side set properties you want to keep. Do note that if you do not select the 'ID' property all user-defined
block and set IDs will be lost in the output file. After the selectors you can also pass in a list of nodal and global
variable IDs to keep and a list of time steps to keep.

Below is a step-by-step process of writing out a subset of a mesh.
1. Create an empty list to contain your `ElementBlockSelectors`.
2. For each element block you want to keep, append an `exodusutils.selector.ElementBlockSelector` for that element
block, selecting the elements you want to keep and any variables or attributes you want to keep.
3. Create an empty list to contain your `SideSetSelectors`.
4. For each side set you want to keep, append a `exodusutils.selector.SideSetSelector` for that side set, selecting the
sides you want to keep as well as any variables you want to keep. *Any element contained in the selected part of the
side set must also be selected in your list of ElementBlockSelectors!*
5. Create an empty list to contain your `NodeSetSelectors`.
6. As before, append a `exodusutils.selector.NodeSetSelector` for each node set containing the nodes and variables you
want to keep.
7. Create a `exodusutils.selector.PropertySelector` and pass in the lists of properties you want to keep per its
constructor.
8. Make a list of all of the nodal and global variable IDs you want to keep.
9. Make a list of all of the time steps you want to keep.
10. Pass all of the lists along with other required arguments to `exodusutils.output_subset.output_subset`.

By default, if you do not pass in an argument to a selector, it selects all applicable items. If you want to quickly do
this explicitly you should pass in `...` and if you want to quickly select nothing you should pass in either an empty
list or `None`. The same applied for the nodal variable ID list, global variable ID list, and time steps list.

If an error occurs during execution of the `output_subset` function, the output file it creates will be corrupt!

```
# We are going to output only the tail of the biplane.
ex = Exodus("sample-files/biplane.exo", 'r')
# Propeller element blocks: 1, 3, 4
eb_sels = [ElementBlockSelector(ex, 1), ElementBlockSelector(ex, 3), ElementBlockSelector(ex, 4)]
# We don't want to keep any node sets or side sets, so leave those lists empty.
# We don't want to lose any properties so we leave the property lists in the
# PropertySelector constructor to their default value (all).
# We want to keep all the variables and time steps, so we leave those
# arguments to their default values
output_subset(ex, "sample-files/w/tail.exo", "Biplane Tail", eb_sels, [], [], PropertySelector(ex))
ex.close()
```
## Adding/Removing/Modifying data in an Exodus II file
To alter an Exodus II file, create the `Exodus` object in append mode (mode='a'). In read mode, calling any functions
that modify the file will cause an error to be thrown. Any modifications you make to the file will only be stored in
memory. When you are done modifying the file you should call the `Exodus` object's `write` function with a path to the
file you would like to output the changes to. You must pass in a new path so that you do not overwrite the source file
and risk losing important data.

All of the functions in `exodusutils.exodus.Exodus` below the diff functions modify the file and require append mode.

This library does not currently support modifying variables, but you can add and remove nodes/sides from node/side sets
as well as create brand new node/side sets and delete existing ones in addition to adding and removing elements. This
library also supplies helpful functions for splitting side sets and skinning element blocks, both of which result in the
creation of new side sets.

```
# Open the Exodus II file in append mode
ex = Exodus("sample-files/w/tail.exo", 'a')
# Skin the whole mesh and output the side set containing all exterior faces to
# a new side set with ID 3312
# To learn more about skinning, see the tutorial on skinning a mesh
ex.skin(3312, 'Skinned Mesh')
# Split the newly created side set 3312 into side set 1111 containing only
# faces entirely to the right of x=0.849 and 222 containing those to the
# left of x=0.849 without deleting side set 3312
ex.split_side_set_x_coords(3312, '>=', 0.849, True, 1111, 2222, False)
# Now that we have made changes to the file, write those changes to a new
# file called "tail-skinned.exo"
ex.write("sample-files/w/tail-skinned.exo")
# We've written our changes so now we can safely close the original file
# without losing our progress
ex.close()
```
## Skinning a mesh
In some cases, you may want to work with only the exterior faces of a mesh. Skinning a mesh creates a side set
containing all the exterior faces of the mesh or selected element block. See the `exodusutils.exodus.Exodus.skin` and
`exodusutils.exodus.Exodus.skin_element_block` functions for more information.

To use the skinning functions, create the `Exodus` object in append mode. When the functions successfully complete, they
will create a new side set with the specified ID and name. Remember to call the `write` function afterwards in order to
write these changes to a new Exodus II file.

Exodus II files are inconsistent in the definition of some topographical features, especially tris. When calling a skin
function, you can specify whether the "TRI" prefix of an element block's topography attribute refers to a normal TRI or
a TRISHELL.

The skinning functions may encounter problems with certain element types, namely shells. If an element block does not
skin properly, it may be due to an unsupported element type.
"""

from .exodus import Exodus
from .output_subset import output_subset
from .selector import ElementBlockSelector, SideSetSelector, NodeSetSelector, PropertySelector
from .constants import (
    # Object types
    ELEMBLOCK,
    NODESET,
    SIDESET,
    # Variable types
    GLOBAL_VAR,
    NODAL_VAR,
    ELEMENTAL_VAR,
    NODESET_VAR,
    SIDESET_VAR
)
