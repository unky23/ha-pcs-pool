from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class PCSSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def _pump_mode(controller: dict[str, Any]) -> str:
    try:
        return "auto" if int(controller.get("ma1")) == 1 else "ręczny"
    except Exception:
        return "nieznany"


SENSOR_DESCRIPTIONS: tuple[PCSSensorDescription, ...] = (
    PCSSensorDescription(
        key="ph",
        translation_key="ph",
        native_unit_of_measurement="pH",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:ph",
        value_fn=lambda c: c.get("p"),
    ),
    PCSSensorDescription(
        key="redox",
        translation_key="redox",
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle",
        value_fn=lambda c: c.get("r"),
    ),
    PCSSensorDescription(
        key="chlorine",
        translation_key="chlorine",
        native_unit_of_measurement="mg/L",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chemical-weapon",
        value_fn=lambda c: c.get("c"),
    ),
    PCSSensorDescription(
        key="chlorine_bound",
        translation_key="chlorine_bound",
        native_unit_of_measurement="mg/L",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chemical-weapon",
        value_fn=lambda c: c.get("cz"),
    ),
    PCSSensorDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class="temperature",
        value_fn=lambda c: c.get("te"),
    ),
    PCSSensorDescription(
        key="flow",
        translation_key="flow",
        native_unit_of_measurement="L/min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:waves-arrow-right",
        value_fn=lambda c: c.get("mo1"),
    ),
    PCSSensorDescription(
        key="salt",
        translation_key="salt",
        native_unit_of_measurement="g/L",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shaker-outline",
        value_fn=lambda c: c.get("s"),
    ),
    PCSSensorDescription(
        key="pump_mode",
        translation_key="pump_mode",
        icon="mdi:pump",
        value_fn=_pump_mode,
    ),
    PCSSensorDescription(
        key="last_seen",
        translation_key="last_seen",
        icon="mdi:clock-outline",
        value_fn=lambda c: c.get("kd"),
    ),
    PCSSensorDescription(
        key="controller_name",
        translation_key="controller_name",
        icon="mdi:chip",
        value_fn=lambda c: _clean(c.get("kn")),
    ),
    PCSSensorDescription(
        key="location",
        translation_key="location",
        icon="mdi:map-marker",
        value_fn=lambda c: _clean(c.get("kl")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        PCSSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class PCSSensor(CoordinatorEntity, SensorEntity):
    entity_description: PCSSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: PCSSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self):
        data = self.coordinator.data or {}
        controller_id = data.get("kid") or "pcs_pool_controller"

        return {
            "identifiers": {(DOMAIN, str(controller_id))},
            "name": data.get("kn") or "PCS Pool Controller",
            "manufacturer": "PCS / PoolCS",
            "model": "PCS API Controller",
            "sw_version": str(data.get("kv")) if data.get("kv") is not None else None,
            "suggested_area": data.get("kl"),
        }

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}

        return {
            "controller_id": data.get("kid"),
            "controller_name": data.get("kn"),
            "location": data.get("kl"),
            "object_id": data.get("wid"),
            "object_name": data.get("wn"),
            "last_seen": data.get("kd"),
        }
