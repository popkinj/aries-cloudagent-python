from aries_cloudagent.tests import mock
from unittest import IsolatedAsyncioTestCase

from ......core.oob_processor import OobMessageProcessor
from ......messaging.request_context import RequestContext
from ......messaging.responder import MockResponder
from ......transport.inbound.receipt import MessageReceipt

from ...messages.cred_issue import V20CredIssue

from .. import cred_issue_handler as test_module


class TestCredentialIssueHandler(IsolatedAsyncioTestCase):
    async def test_called(self):
        request_context = RequestContext.test_context()
        request_context.message_receipt = MessageReceipt()
        request_context.settings["debug.auto_store_credential"] = False
        request_context.connection_record = mock.MagicMock()

        mock_oob_processor = mock.MagicMock(
            find_oob_record_for_inbound_message=mock.CoroutineMock(
                return_value=mock.MagicMock()
            )
        )
        request_context.injector.bind_instance(OobMessageProcessor, mock_oob_processor)

        with mock.patch.object(
            test_module, "V20CredManager", autospec=True
        ) as mock_cred_mgr:
            mock_cred_mgr.return_value.receive_credential = mock.CoroutineMock()
            request_context.message = V20CredIssue()
            request_context.connection_ready = True
            handler_inst = test_module.V20CredIssueHandler()
            responder = MockResponder()
            await handler_inst.handle(request_context, responder)

        mock_cred_mgr.assert_called_once_with(request_context.profile)
        mock_cred_mgr.return_value.receive_credential.assert_called_once_with(
            request_context.message, request_context.connection_record.connection_id
        )
        mock_oob_processor.find_oob_record_for_inbound_message.assert_called_once_with(
            request_context
        )
        assert not responder.messages

    async def test_called_auto_store(self):
        request_context = RequestContext.test_context()
        request_context.message_receipt = MessageReceipt()
        request_context.settings["debug.auto_store_credential"] = True
        request_context.connection_record = mock.MagicMock()

        mock_oob_processor = mock.MagicMock(
            find_oob_record_for_inbound_message=mock.CoroutineMock(
                return_value=mock.MagicMock()
            )
        )
        request_context.injector.bind_instance(OobMessageProcessor, mock_oob_processor)

        with mock.patch.object(
            test_module, "V20CredManager", autospec=True
        ) as mock_cred_mgr:
            mock_cred_mgr.return_value = mock.MagicMock(
                receive_credential=mock.CoroutineMock(),
                store_credential=mock.CoroutineMock(),
                send_cred_ack=mock.CoroutineMock(return_value="cred_ack_message"),
            )
            request_context.message = V20CredIssue()
            request_context.connection_ready = True
            handler_inst = test_module.V20CredIssueHandler()
            responder = MockResponder()
            await handler_inst.handle(request_context, responder)

        mock_cred_mgr.assert_called_once_with(request_context.profile)
        mock_cred_mgr.return_value.receive_credential.assert_called_once_with(
            request_context.message, request_context.connection_record.connection_id
        )
        mock_oob_processor.find_oob_record_for_inbound_message.assert_called_once_with(
            request_context
        )
        assert mock_cred_mgr.return_value.send_cred_ack.call_count == 1

    async def test_called_auto_store_x(self):
        request_context = RequestContext.test_context()
        request_context.message_receipt = MessageReceipt()
        request_context.settings["debug.auto_store_credential"] = True
        request_context.connection_record = mock.MagicMock()

        mock_oob_processor = mock.MagicMock(
            find_oob_record_for_inbound_message=mock.CoroutineMock(
                return_value=mock.MagicMock()
            )
        )
        request_context.injector.bind_instance(OobMessageProcessor, mock_oob_processor)

        with mock.patch.object(
            test_module, "V20CredManager", autospec=True
        ) as mock_cred_mgr:
            mock_cred_mgr.return_value = mock.MagicMock(
                receive_credential=mock.CoroutineMock(
                    return_value=mock.MagicMock(save_error_state=mock.CoroutineMock())
                ),
                store_credential=mock.CoroutineMock(
                    side_effect=[
                        test_module.IndyHolderError,
                        test_module.StorageError(),
                    ]
                ),
                send_cred_ack=mock.CoroutineMock(),
            )

            request_context.message = V20CredIssue()
            request_context.connection_ready = True
            handler_inst = test_module.V20CredIssueHandler()
            responder = MockResponder()

            await handler_inst.handle(request_context, responder)  # holder error
            await handler_inst.handle(request_context, responder)  # storage error
            assert mock_cred_mgr.return_value.send_cred_ack.call_count == 2

    async def test_called_not_ready(self):
        request_context = RequestContext.test_context()
        request_context.message_receipt = MessageReceipt()
        request_context.connection_record = mock.MagicMock()

        with mock.patch.object(
            test_module, "V20CredManager", autospec=True
        ) as mock_cred_mgr:
            mock_cred_mgr.return_value.receive_credential = mock.CoroutineMock()
            request_context.message = V20CredIssue()
            request_context.connection_ready = False
            handler_inst = test_module.V20CredIssueHandler()
            responder = MockResponder()
            with self.assertRaises(test_module.HandlerException) as err:
                await handler_inst.handle(request_context, responder)
            assert err.exception.message == "Connection used for credential not ready"

        assert not responder.messages

    async def test_called_no_connection_no_oob(self):
        request_context = RequestContext.test_context()
        request_context.message_receipt = MessageReceipt()

        mock_oob_processor = mock.MagicMock(
            find_oob_record_for_inbound_message=mock.CoroutineMock(
                # No oob record found
                return_value=None
            )
        )
        request_context.injector.bind_instance(OobMessageProcessor, mock_oob_processor)

        request_context.message = V20CredIssue()
        handler_inst = test_module.V20CredIssueHandler()
        responder = MockResponder()
        with self.assertRaises(test_module.HandlerException) as err:
            await handler_inst.handle(request_context, responder)
        assert (
            err.exception.message
            == "No connection or associated connectionless exchange found for credential"
        )

        assert not responder.messages
