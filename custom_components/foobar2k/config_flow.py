import asyncio
import logging
import voluptuous as vol

from async_timeout import timeout
from aiohttp import ClientError, web_exceptions

from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN, TIMEOUT
from .foobar2k import Foobar2k

_LOGGER = logging.getLogger(__name__)


class Foobar2kConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Foobar2k config flow."""

    VERSION = 1

    @core.callback
    def _async_get_entry(self, data):

        return self.async_create_entry(
            title=data[CONF_HOST],
            data={
                CONF_HOST: data[CONF_HOST],
                CONF_PORT: data.get(CONF_PORT)
            },
        )

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("async_step_user")
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self.schema)

        errors = {}
        host = user_input[CONF_HOST]
        port = user_input.get(CONF_PORT) or DEFAULT_PORT
        user_input = {**user_input, CONF_PORT: port}

        session = async_get_clientsession(self.hass)
        fb2k_api = Foobar2k(session, host, port, TIMEOUT)
        # Reject duplicates *before* contacting the server — saves an HTTP
        # roundtrip and keeps the AbortFlow out of the connect-error handlers
        # below (which would otherwise swallow it as "device_fail").
        await self.async_set_unique_id(fb2k_api.unique_id)
        self._abort_if_unique_id_configured()

        try:
            _LOGGER.debug("create_device")
            async with timeout(TIMEOUT):
                _LOGGER.debug("Call Foobar2k")
                await fb2k_api.async_update()
        except asyncio.TimeoutError:
            return self.async_show_form(
                step_id="user",
                data_schema=self.schema,
                errors={"base": "device_timeout"},
            )
        except web_exceptions.HTTPForbidden:
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "forbidden"},
            )
        except ClientError:
            _LOGGER.exception("ClientError")
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "device_fail"},
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating device")
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "device_fail"},
            )

        _LOGGER.debug(f"Device {fb2k_api.unique_id} has been setup")

        return self._async_get_entry(user_input)

    @property
    def schema(self):
        """Return current schema."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )