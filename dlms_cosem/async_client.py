"""Async DLMS/COSEM client."""
from __future__ import annotations

import asyncio
from typing import Any, Generator, List, Optional, Union

import attr
import structlog

from dlms_cosem import cosem, dlms_data, enumerations, exceptions, state, utils
from dlms_cosem.connection import DlmsConnection, DlmsConnectionSettings
from dlms_cosem.cosem.selective_access import EntryDescriptor, RangeDescriptor
from dlms_cosem.protocol import acse, xdlms
from dlms_cosem.protocol.xdlms import ConfirmedServiceError
from dlms_cosem.security import AuthenticationMethodManager

LOG = structlog.get_logger()

# Re-export for convenience
DataResultError = exceptions.DataResultError
ActionError = exceptions.ActionError
HLSError = exceptions.HLSError


@attr.s(auto_attribs=True)
class AsyncDlmsClient:
    """Asynchronous DLMS/COSEM client.

    API-compatible with DlmsClient but all methods are coroutines.
    Uses asyncio.Lock to serialize HDLC half-duplex requests while
    allowing concurrent coroutine scheduling.
    """

    transport: Any  # DlmsTransport
    authentication: AuthenticationMethodManager
    encryption_key: Optional[bytes] = attr.ib(default=None)
    authentication_key: Optional[bytes] = attr.ib(default=None)
    security_suite: Optional[int] = attr.ib(default=0)
    dedicated_ciphering: bool = attr.ib(default=False)
    block_transfer: bool = attr.ib(default=False)
    max_pdu_size: int = attr.ib(default=65535)
    client_system_title: Optional[bytes] = attr.ib(default=None)
    client_initial_invocation_counter: int = attr.ib(default=0)
    meter_initial_invocation_counter: int = attr.ib(default=0)
    timeout: int = attr.ib(default=10)
    invoke_id: int = attr.ib(default=0)
    invoke_id_confirmed: bool = attr.ib(default=True)
    invoke_id_high_priority: bool = attr.ib(default=True)
    connection_settings: Optional[DlmsConnectionSettings] = attr.ib(default=None)

    dlms_connection: DlmsConnection = attr.ib(
        default=attr.Factory(
            lambda self: DlmsConnection(
                client_system_title=self.client_system_title,
                authentication=self.authentication,
                global_encryption_key=self.encryption_key,
                global_authentication_key=self.authentication_key,
                use_dedicated_ciphering=self.dedicated_ciphering,
                use_block_transfer=self.block_transfer,
                security_suite=self.security_suite,
                max_pdu_size=self.max_pdu_size,
                client_invocation_counter=self.client_initial_invocation_counter,
                meter_invocation_counter=self.meter_initial_invocation_counter,
                settings=self.connection_settings,
            ),
            takes_self=True,
        )
    )

    def __attrs_post_init__(self):
        self._lock = asyncio.Lock()

    async def session(self) -> Any:
        """Async context manager for a DLMS session."""
        return self._AsyncSession(self)

    def next_invoke_id(self) -> int:
        current = self.invoke_id
        self.invoke_id = (current + 1) % 16
        return current

    def next_invoke_id_and_priority(self) -> xdlms.InvokeIdAndPriority:
        return xdlms.InvokeIdAndPriority(
            invoke_id=self.next_invoke_id(),
            confirmed=self.invoke_id_confirmed,
            high_priority=self.invoke_id_high_priority,
        )

    async def connect(self) -> None:
        self.transport.connect()

    async def disconnect(self) -> None:
        self.transport.disconnect()

    async def send(self, *events) -> None:
        """Send event(s) over the transport. Must be called under lock."""
        for event in events:
            data = self.dlms_connection.send(event)
            response_bytes = self.transport.send_request(data)
            self.dlms_connection.receive_data(response_bytes)

    def next_event(self):
        """Parse next event from the DLMS connection buffer (sync)."""
        return self.dlms_connection.next_event()

    async def associate(
        self,
        association_request: Optional[acse.ApplicationAssociationRequest] = None,
    ) -> acse.ApplicationAssociationResponse:
        aarq = association_request or self.dlms_connection.get_aarq()

        async with self._lock:
            await self.send(aarq)
            response = self.next_event()

        if isinstance(response, xdlms.ExceptionResponse):
            raise exceptions.DlmsClientException(
                f"DLMS Exception: {response.state_error!r}:{response.service_error!r}"
            )
        if isinstance(response, acse.ApplicationAssociationResponse):
            if response.result is not enumerations.AssociationResult.ACCEPTED:
                extra_error = None
                if response.user_information:
                    if isinstance(
                        response.user_information.content, ConfirmedServiceError
                    ):
                        extra_error = response.user_information.content.error
                raise exceptions.DlmsClientException(
                    f"Unable to perform Association: {response.result!r} and "
                    f"{response.result_source_diagnostics!r}, extra info: {extra_error}"
                )
        else:
            raise exceptions.LocalDlmsProtocolError(
                "Did not receive an AARE after sending AARQ"
            )

        if self._should_send_hls_reply():
            try:
                hls_response = await self._perform_hls_reply()
            except ActionError as e:
                raise HLSError from e
            if not hls_response:
                raise HLSError("No HLS data in response")
            hls_data = utils.parse_as_dlms_data(hls_response)
            if not hls_data:
                raise HLSError("Did not receive any HLS response data")
            if not self.dlms_connection.authentication.hls_meter_data_is_valid(
                hls_data, self.dlms_connection
            ):
                raise HLSError("Meter did not respond with correct challenge calculation")

        return response

    def _should_send_hls_reply(self) -> bool:
        return (
            self.dlms_connection.state.current_state
            == state.SHOULD_SEND_HLS_SEVER_CHALLENGE_RESULT
        )

    async def _perform_hls_reply(self) -> Optional[bytes]:
        return await self.action(
            method=cosem.CosemMethod(
                enumerations.CosemInterface.ASSOCIATION_LN,
                cosem.Obis(0, 0, 40, 0, 0),
                1,
            ),
            data=dlms_data.OctetStringData(
                self.dlms_connection.authentication.hls_generate_reply_data(
                    self.dlms_connection
                )
            ).to_bytes(),
        )

    async def get(
        self,
        cosem_attribute: cosem.CosemAttribute,
        access_descriptor: Optional[Union[RangeDescriptor, EntryDescriptor]] = None,
    ) -> bytes:
        invoke = self.next_invoke_id_and_priority()
        async with self._lock:
            await self.send(
                xdlms.GetRequestNormal(
                    cosem_attribute=cosem_attribute,
                    access_selection=access_descriptor,
                    invoke_id_and_priority=invoke,
                )
            )
            all_data_received = False
            data = bytearray()
            while not all_data_received:
                get_response = self.next_event()
                if isinstance(get_response, xdlms.GetResponseNormal):
                    data.extend(get_response.data)
                    all_data_received = True
                    continue
                if isinstance(get_response, xdlms.GetResponseWithBlock):
                    data.extend(get_response.data)
                    await self.send(
                        xdlms.GetRequestNext(
                            invoke_id_and_priority=get_response.invoke_id_and_priority,
                            block_number=get_response.block_number,
                        )
                    )
                    continue
                if isinstance(get_response, xdlms.GetResponseLastBlock):
                    data.extend(get_response.data)
                    all_data_received = True
                    continue
                if isinstance(get_response, xdlms.GetResponseLastBlockWithError):
                    raise DataResultError(
                        f"Error in blocktransfer of GET response: {get_response.error!r}"
                    )
                if isinstance(get_response, xdlms.GetResponseNormalWithError):
                    raise DataResultError(
                        f"Could not perform GET request: {get_response.error!r}"
                    )
        return bytes(data)

    async def get_many(
        self, cosem_attributes_with_selection: List[cosem.CosemAttributeWithSelection]
    ):
        invoke = self.next_invoke_id_and_priority()
        out = xdlms.GetRequestWithList(
            cosem_attributes_with_selection=cosem_attributes_with_selection,
            invoke_id_and_priority=invoke,
        )
        async with self._lock:
            await self.send(out)
            response = self.next_event()
        if isinstance(response, xdlms.ExceptionResponse):
            raise exceptions.DlmsClientException(
                f"Received an Exception response with state error: "
                f"{response.state_error.name} and service error: "
                f"{response.service_error.name}"
            )
        return response

    async def get_with_range(
        self,
        cosem_attribute: cosem.CosemAttribute,
        from_value,
        to_value,
        restricting_object: Optional[cosem.CosemAttribute] = None,
    ) -> bytes:
        from dlms_cosem.cosem.capture_object import CaptureObject

        if restricting_object is None:
            restricting_object = cosem.CosemAttribute(
                interface=cosem_attribute.interface,
                instance=cosem_attribute.instance,
                attribute=3,
            )

        restricting_capture_object = CaptureObject(
            cosem_attribute=restricting_object,
            data_index=0,
        )

        access_descriptor = RangeDescriptor(
            restricting_object=restricting_capture_object,
            from_value=from_value,
            to_value=to_value,
        )

        return await self.get(cosem_attribute, access_descriptor=access_descriptor)

    async def get_with_entry(
        self,
        cosem_attribute: cosem.CosemAttribute,
        from_entry: int = 1,
        to_entry: int = 0,
        from_selected_value: int = 1,
        to_selected_value: int = 0,
    ) -> bytes:
        access_descriptor = EntryDescriptor(
            from_entry=from_entry,
            to_entry=to_entry,
            from_selected_value=from_selected_value,
            to_selected_value=to_selected_value,
        )
        return await self.get(cosem_attribute, access_descriptor=access_descriptor)

    async def set(self, cosem_attribute: cosem.CosemAttribute, data: bytes):
        invoke = self.next_invoke_id_and_priority()
        async with self._lock:
            await self.send(
                xdlms.SetRequestNormal(
                    cosem_attribute=cosem_attribute,
                    data=data,
                    invoke_id_and_priority=invoke,
                )
            )
            return self.next_event()

    async def action(self, method: cosem.CosemMethod, data: bytes):
        invoke = self.next_invoke_id_and_priority()
        async with self._lock:
            await self.send(
                xdlms.ActionRequestNormal(
                    cosem_method=method,
                    data=data,
                    invoke_id_and_priority=invoke,
                )
            )
            response = self.next_event()

        if isinstance(response, xdlms.ActionResponseNormalWithError):
            raise ActionError(response.error.name)
        elif isinstance(response, xdlms.ActionResponseNormalWithData):
            if response.status != enumerations.ActionResultStatus.SUCCESS:
                raise ActionError(f"Unsuccessful ActionRequest: {response.status.name}")
            return response.data
        else:
            if response.status != enumerations.ActionResultStatus.SUCCESS:
                raise ActionError(f"Unsuccessful ActionRequest: {response.status.name}")
        return

    async def release_association(self) -> Optional[acse.ReleaseResponse]:
        rlrq = self.dlms_connection.get_rlrq()
        try:
            async with self._lock:
                await self.send(rlrq)
                rlre = self.next_event()
            return rlre
        except exceptions.NoRlrqRlreError:
            return None

    async def close(self) -> None:
        """Close the connection."""
        try:
            await self.release_association()
        except Exception:
            pass
        await self.disconnect()

    @property
    def client_invocation_counter(self) -> int:
        return self.dlms_connection.client_invocation_counter

    @client_invocation_counter.setter
    def client_invocation_counter(self, ic: int):
        self.dlms_connection.client_invocation_counter = ic


class _AsyncSession:
    """Async context manager for DLMS sessions."""

    def __init__(self, client: AsyncDlmsClient):
        self._client = client

    async def __aenter__(self) -> AsyncDlmsClient:
        await self._client.connect()
        await self._client.associate()
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.release_association()
        await self._client.disconnect()
