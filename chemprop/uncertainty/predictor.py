from abc import abstractmethod
from typing import Iterable

import numpy as np

from lightning import pytorch as pl
from torch import Tensor
from torch.utils.data import DataLoader

from chemprop.models.model import MPNN
from chemprop.utils.registry import ClassRegistry


class UncertaintyPredictor:
    def __call__(self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer):
        return self._calc_prediction_uncertainty(dataloader, models, trainer)

    @abstractmethod
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        """
        Calculate the uncalibrated predictions and uncertainties for the dataloader.
        """
        pass


UncertaintyPredictorRegistry = ClassRegistry[UncertaintyPredictor]()


@UncertaintyPredictorRegistry.register(None)
class NoUncertaintyPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("mve")
class MVEPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("ensemble")
class EnsemblePredictor(UncertaintyPredictor):
    """
    Class that predicts uncertainty for predictions based on the variance in predictions among
    an ensemble's submodels.
    """
    def __init__(self, individual_ensemble_predictions):
        self.individual_ensemble_predictions = individual_ensemble_predictions

    def _calc_prediction_uncertainty(self, dataloader, models, trainer) -> Tensor:
        if len(models) == 1:
            raise ValueError(
                "Ensemble method for uncertainty is only available when multiple models are provided."
            )
        individual_preds = []
        for model in models:
            predss = trainer.predict(model, dataloader)
            preds = torch.concat(predss, 0)
            if isinstance(model.predictor, MulticlassClassificationFFN):
                preds = torch.argmax(preds, dim=-1)
            individual_preds.append(preds)
        stacked_preds = torch.stack(individual_preds).float()
        means = torch.mean(stacked_preds, dim=0)
        vars = torch.var(stacked_preds, dim=0, correction=0)
        return means, vars


@UncertaintyPredictorRegistry.register("classification")
class ClassPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("evidential-total")
class EvidentialTotalPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("evidential-epistemic")
class EvidentialEpistemicPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("evidential-aleatoric")
class EvidentialAleatoricPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("dropout")
class DropoutPredictor(UncertaintyPredictor):
    """
    Class that creates an artificial ensemble of models by applying monte carlo dropout to the loaded
    model parameters. Predicts uncertainty for predictions based on the variance in predictions among
    an ensemble's submodels.
    """

    def __init__(self, sampling_size, dropout_p):
        self.sampling_size = sampling_size
        self.dropout_p = dropout_p

    def _calc_prediction_uncertainty(self, dataloader, models, trainer) -> Tensor:
        # TODO: uses first model if multiple are given, should throw error if multiple are given.
        model = next(iter(models))
        model.apply(self.activate_dropout)

        for i in range(self.sampling_size):
            preds = trainer.predict(model, dataloader)
            if i == 0:
                sum_preds = np.array(preds)
                sum_squared = np.square(preds)
            else:
                sum_preds += np.array(preds)
                sum_squared += np.square(preds)

        uncal_preds = sum_preds / self.sampling_size
        uncal_vars = (
            sum_squared / self.sampling_size
            - np.square(sum_preds) / self.sampling_size**2
        )

        return (
            uncal_preds.tolist(),
            uncal_vars.tolist(),
        )

    def activate_dropout(self, module):
        if isinstance(module, nn.Dropout):
            module.p = self.dropout_p
            module.train()

@UncertaintyPredictorRegistry.register("spectra-roundrobin")
class RoundRobinSpectraPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("dirichlet")
class DirichletPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("conformal-quantile-regression")
class ConformalQuantileRegressionPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return


@UncertaintyPredictorRegistry.register("conformal-regression")
class ConformalRegressionPredictor(UncertaintyPredictor):
    def _calc_prediction_uncertainty(
        self, dataloader: DataLoader, models: Iterable[MPNN], trainer: pl.Trainer
    ) -> Tensor:
        ...
        return
