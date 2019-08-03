from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import torch
from torch._ops import ops
from torch.nn.modules import Module

_FLOAT_MODULES = {
    torch.add: ops.quantized.add
}

class WrapperModule(torch.nn.Module):
    def __init__(self, operation):
        super(WrapperModule, self).__init__()
        self.operation = operation

    def forward(self, x):
        return self.operation(*x)


class QuantizedWrapperModule(torch.nn.Module):
    def __init__(self, operation):
        super(WrapperModule, self).__init__()
        self.operation = operation
        self.register_buffer('scale', torch.tensor([1.0], dtype=torch.double))
        self.register_buffer('zero_point', torch.tensor([0], dtype=torch.long))

    def forward(self, x):
        return self.operation(*x, scale=self.scale, zero_point=self.zero_point)

    @classmethod
    def from_float(cls, mod, qconfig=None):
        assert (hasattr(mod, 'observer')), \
            "Input float module must have observer attached"
        assert (type(mod) == WrapperModule), \
            "nnq.QuantizedWrapperModule.from_float only works for " \
            + "nnq.WrapperModule"
        qoperation = _FLOAT_MODULES.get(mod.operation, None)
        assert (qoperation is not None), "No quantized operation for " \
            + type(mode.operation)

        scale, zero_point = mod.observer.calculate_qparams()[:2]
        mod = cls(qoperation)
        mod.scale = torch.tensor(scale, dtype=torch.double)
        mod.zero_point = torch.tensor(zero_point, dtype=torch.long)
        return mod
