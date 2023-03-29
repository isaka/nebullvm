import os
import platform
import uuid
from pathlib import Path
from typing import Any

import cpuinfo
import psutil

from nebullvm.optional_modules.torch import Module
from nebullvm.optional_modules.torch_xla import torch_xla, xm
from nebullvm.optional_modules.utils import (
    torch_is_available,
    tensorflow_is_available,
)
from nebullvm.tools.base import Device, DeviceType
from nebullvm.tools.pytorch import torch_get_device_name
from nebullvm.tools.tf import tensorflow_get_gpu_name


def generate_model_id(model_name: str):
    return f"{str(uuid.uuid4())}_{hash(model_name)}"


def get_model_name(model: Any):
    if isinstance(model, str) or isinstance(model, Path):
        return str(model)
    else:
        return model.__class__.__name__


def _get_gpu_name() -> str:
    if torch_is_available():
        name = torch_get_device_name()
    elif tensorflow_is_available():
        name = tensorflow_get_gpu_name()
    else:
        name = "Unknown GPU"

    return name


def _get_neuron_device_name() -> str:
    output = os.popen("lshw -businfo").read()
    neuron_name = "Unknown Neuron"
    for line in output.splitlines():
        if "neuron" in line.lower():
            words = line.split(" ")
            if len(words) > 2:
                neuron_name = " ".join(words[-2:])
                break
    return neuron_name


def _get_tpu_device_name() -> str:
    return xm.xla_device_hw(xm.xla_device())


def get_hw_info(device: Device) -> dict:
    hw_info = {
        "cpu": cpuinfo.get_cpu_info()["brand_raw"],
        "operative_system": platform.system(),
        "ram": f"{round(psutil.virtual_memory().total * 1e-9, 2)} GB",
    }
    if device.type is DeviceType.GPU:
        hw_info["gpu"] = _get_gpu_name()
    if device.type is DeviceType.NEURON:
        hw_info["neuron"] = _get_neuron_device_name()
    return hw_info


def read_model_size(model: Any):
    if isinstance(model, str) or isinstance(model, Path):
        size = os.stat(str(model)).st_size
    elif isinstance(model, Module):
        size = sum(
            param.nelement() * param.element_size()
            for param in model.parameters()
        )
    else:
        # we assume it is a tf_model
        size = model.count_params() * 4  # assuming full precision 32 bit
    return f"{round(size * 1e-6, 2)} MB"
