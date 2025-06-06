from typing import Dict, Iterator, Optional, Tuple, overload

from pydantic import Field, field_validator, model_validator
from typing_extensions import Annotated

from everest_models.jobs.shared.models import ModelConfig, PhaseEnum, RootModelConfig


class Phase(ModelConfig):
    options: Annotated[Tuple[PhaseEnum, ...], Field(default=None, description="")]
    value: Annotated[PhaseEnum, Field(default=None, description="")]

    @field_validator("options")
    @classmethod
    def is_not_empty(cls, options):
        assert options is None or options, "Empty 'options' list"
        return options

    @model_validator(mode="before")
    @classmethod
    def is_correct_phase_field(cls, values):
        assert (values.get("options") is None or values.get("options") == []) ^ (
            values.get("value") is None
        ), "'options' key cannot be used in conjunction with 'value' key."
        return values

    def _optimum_index(self, optimizer_value: float, *, thresholds: Iterator) -> int:
        return next(
            index
            for index, threshold in enumerate(thresholds)
            if optimizer_value <= threshold
        )

    def optimum_value(self, optimizer_value: float) -> str:
        if optimizer_value is None:
            return self.value if self.value is None else self.value.value

        options_size = len(self.options)
        return self.options[
            self._optimum_index(
                optimizer_value,
                thresholds=(float(x + 1) / options_size for x in range(options_size)),
            )
        ].value


class Tolerance(ModelConfig):
    value: Annotated[float | None, Field(default=None, description="")]

    def optimum_value(self, optimizer_value: Optional[float]) -> float:
        if optimizer_value is not None:
            return optimizer_value
        return self.value


class Constraints(ModelConfig):
    phase: Annotated[Phase, Field(description="")]
    rate: Annotated[Tolerance, Field(description="", default=Tolerance(value=None))]
    duration: Annotated[Tolerance, Field(description="", default=Tolerance(value=None))]


# WellConstraintConfig = RootModel[Dict[str, Dict[int, Constraints]]]
class WellConstraintConfig(RootModelConfig):
    root: Dict[str, Dict[int, Constraints]]

    def __iter__(self) -> Iterator[str]:  # type: ignore
        return iter(self.root)

    @overload
    def get(self, __key: str) -> Dict[int, Constraints]: ...

    @overload
    def get(
        self, __key: str, __default: Dict[int, Constraints]
    ) -> Dict[int, Constraints]: ...

    def get(
        self, __key: str, __default: Optional[Dict[int, Constraints]] = None
    ) -> Optional[Dict[int, Constraints]]:
        if __default is None:
            return self.root.get(__key)
        return self.root.get(__key, __default)
