import numpy as np

test_string = list("hello, world")
arr = np.empty(33, '|S1')
for i in range(len(test_string)):
    arr[i] = test_string[i]

mask = np.empty(33, bool)
for i in range(33):
    if i < len(test_string):
        mask[i] = False
    else:
        mask[i] = True

out = np.ma.core.MaskedArray(arr, mask)
print(out)
