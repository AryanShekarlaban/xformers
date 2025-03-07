# Copyright (c) Facebook, Inc. and its affiliates. All rights reserved.
#
# This source code is licensed under the BSD license found in the
# LICENSE file in the root directory of this source tree.

import logging

import torch

# Please update the doc version in docs/source/conf.py as well.
__version__ = "0.0.9"

_is_sparse_available = True
_is_triton_available = torch.cuda.is_available()


def _register_extensions():
    import importlib
    import os

    import torch

    # load the custom_op_library and register the custom ops
    lib_dir = os.path.dirname(__file__)
    if os.name == "nt":
        # Register the main torchvision library location on the default DLL path
        import ctypes
        import sys

        kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
        with_load_library_flags = hasattr(kernel32, "AddDllDirectory")
        prev_error_mode = kernel32.SetErrorMode(0x0001)

        if with_load_library_flags:
            kernel32.AddDllDirectory.restype = ctypes.c_void_p

        if sys.version_info >= (3, 8):
            os.add_dll_directory(lib_dir)
        elif with_load_library_flags:
            res = kernel32.AddDllDirectory(lib_dir)
            if res is None:
                err = ctypes.WinError(ctypes.get_last_error())
                err.strerror += f' Error adding "{lib_dir}" to the DLL directories.'
                raise err

        kernel32.SetErrorMode(prev_error_mode)

    loader_details = (
        importlib.machinery.ExtensionFileLoader,
        importlib.machinery.EXTENSION_SUFFIXES,
    )

    extfinder = importlib.machinery.FileFinder(lib_dir, loader_details)
    ext_specs = extfinder.find_spec("_C")
    if ext_specs is None:
        raise ImportError
    torch.ops.load_library(ext_specs.origin)


if _is_sparse_available:
    try:
        _register_extensions()
    except (ImportError, OSError) as e:
        print(e)
        logging.warning(
            f"WARNING: {e}\nNeed to compile C++ extensions to get sparse attention suport."
            + " Please run python setup.py build develop"
        )
        _is_sparse_available = False


if _is_triton_available:
    try:
        from xformers.triton.softmax import softmax as triton_softmax  # noqa
    except ImportError as e:
        logging.warning(
            f"Triton is not available, some optimizations will not be enabled.\nError {e}"
        )
        _is_triton_available = False
