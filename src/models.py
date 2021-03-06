from functools import partial

import torch
import torch.nn as nn
import numpy as np
from loguru import logger

from . import utils


def init_weights(layer, std=np.sqrt(2), bias_const=0.0):
    """
    Initialize layer with orthogonal matrices
    """
    if isinstance(layer, nn.Linear):
        nn.init.orthogonal_(layer.weight, std)
        nn.init.constant_(layer.bias, bias_const)
    return layer


class MLP(nn.Module):
    """
    Multi-layer perceptron to be used with columnar-type
    fixed-size input vectors
    """

    def __init__(
        self,
        input_size,
        hidden_dims,
        output_size,
        non_linearity=nn.LeakyReLU,
        log_softmax=True,
    ):
        assert isinstance(
            input_size, int
        ), "Input dimensions should be given as an integer"
        assert isinstance(
            hidden_dims, list
        ), "Hidden dimensions should be given as a list of integers"
        assert isinstance(
            output_size, int
        ), "Output dimensions should be given as an integer"
        super(MLP, self).__init__()

        # Define architecture
        hidden_dims = [*hidden_dims, output_size]
        linear_layers = [nn.Linear(input_size, hidden_dims[0]), non_linearity()]
        for h in range(1, len(hidden_dims)):
            linear_layers += [
                nn.Linear(hidden_dims[h - 1], hidden_dims[h]),
                non_linearity(),
            ]
        self.mlp = nn.Sequential(*linear_layers)
        self.log_softmax = log_softmax

        # Print model summary
        logger.debug(f"Model summary: {self}")

        # Orthogonal initialization
        self.apply(init_weights)

        # Transfer to device
        self.to(utils.get_torch_device())

    def forward(self, x, mask=None):
        """
        Perform a single example or batch forward pass
        """
        start_dim = 0 if not self.training else 1
        x = self.mlp(torch.flatten(x, start_dim=start_dim))
        if not self.log_softmax:
            return x
        return utils.masked_log_softmax(x, mask=mask, dim=-1)

    def get_gradient_norm(self, norm_type=2.0):
        """
        Compute the norm of the gradient w.r.t. the network parameters,
        after calling loss.backward

        https://pytorch.org/docs/stable/_modules/torch/nn/utils/clip_grad.html#clip_grad_norm_
        """
        norm = 0.0
        parameters = [
            p for p in self.parameters() if p.grad is not None and p.requires_grad
        ]
        if len(parameters) > 0:
            device = parameters[0].grad.device
            norm = torch.norm(
                torch.stack(
                    [
                        torch.norm(p.grad.detach(), norm_type).to(device)
                        for p in parameters
                    ]
                ),
                norm_type,
            ).item()
        return norm
