import torch
from torch import nn


class EEGNetBaseline(nn.Module):
    """
    Compact EEGNet-style baseline.

    Input:
        (batch_size, channels, time_samples)

    Output:
        Two class logits: non-stress and stress.

    This is NOT a WS-KAN-EEGNet implementation.
    """

    def __init__(
        self,
        n_channels,
        n_times,
        n_classes=2,
        dropout=0.5,
        F1=8,
        D=2,
        F2=16,
        kernel_length=64
    ):
        super().__init__()

        self.temporal = nn.Sequential(
            nn.Conv2d(
                1,
                F1,
                kernel_size=(1, kernel_length),
                padding=(0, kernel_length // 2),
                bias=False
            ),
            nn.BatchNorm2d(F1)
        )

        self.spatial = nn.Sequential(
            nn.Conv2d(
                F1,
                F1 * D,
                kernel_size=(n_channels, 1),
                groups=F1,
                bias=False
            ),
            nn.BatchNorm2d(F1 * D),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 4)),
            nn.Dropout(dropout)
        )

        self.temporal_depthwise = nn.Sequential(
            nn.Conv2d(
                F1 * D,
                F1 * D,
                kernel_size=(1, 16),
                padding=(0, 8),
                groups=F1 * D,
                bias=False
            ),
            nn.Conv2d(
                F1 * D,
                F2,
                kernel_size=(1, 1),
                bias=False
            ),
            nn.BatchNorm2d(F2),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 8)),
            nn.Dropout(dropout)
        )

        # Calculate the classifier input size.
        with torch.no_grad():
            dummy = torch.zeros(
                1, 1, n_channels, n_times
            )

            feature_count = (
                self._features(dummy)
                .flatten(1)
                .shape[1]
            )

        self.classifier = nn.Linear(
            feature_count,
            n_classes
        )

    def _features(self, x):
        x = self.temporal(x)
        x = self.spatial(x)
        x = self.temporal_depthwise(x)
        return x

    def forward(self, x):
        # (batch, channels, time)
        x = x.unsqueeze(1)

        features = self._features(x)

        return self.classifier(
            features.flatten(1)
        )