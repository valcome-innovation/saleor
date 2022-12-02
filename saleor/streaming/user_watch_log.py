import datetime

import boto3
import graphene
import json
import boto3.exceptions
import logging

from django.core.management.utils import get_random_secret_key

from .models import StreamTicket
from ..streaming import stream_settings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def create_user_watch_log_from_stream_ticket(stream_ticket: "StreamTicket"):
    # user watch logs will only be created for single tickets
    if stream_ticket.game_id is not None:
        send_user_watch_log_to_kinesis_stream(stream_ticket)


def send_user_watch_log_to_kinesis_stream(stream_ticket: "StreamTicket"):
    try:
        credentials = retrieve_cognito_credentials()
        kinesis = create_kinesis_client(credentials)
        user_watch_log = create_user_watch_log(stream_ticket)
        put_stream_record(kinesis, user_watch_log)
    except Exception as exc:
        logger.exception(
            f"[AWS Kinesis] Couldn't create user watch log "
            f"for stream_ticket={stream_ticket.id}",
            exc_info=exc
        )


def retrieve_cognito_credentials():
    cognito = boto3.client('cognito-identity')
    identity_id = retrieve_identity_id(cognito)
    identity_credentials = cognito.get_credentials_for_identity(IdentityId=identity_id)
    return identity_credentials["Credentials"]


def retrieve_identity_id(cognito):
    identity_id_result = cognito.get_id(
        AccountId="487554623251", IdentityPoolId="eu-central-1:671684ed-6f0f-4450-9e19-cef66fb5f68a"
    )
    return identity_id_result["IdentityId"]


def create_kinesis_client(credentials):
    return boto3.client(
        'kinesis',
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretKey"],
        aws_session_token=credentials["SessionToken"])


def create_user_watch_log(stream_ticket: "StreamTicket"):
    user = stream_ticket.user
    global_user_id = graphene.Node.to_global_id("User", user.id)

    return {
        'gameId': f'{stream_ticket.game_id}',
        'userId': f'{global_user_id}',
        'streamTicketId': stream_ticket.id,
        'favoriteTeamId': user.favorite_team,
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
        'hideInAnalytics': False,
        'type': 'ticket',
        'watchDuration': 0,
        'watchThresholdReached': False
    }


def put_stream_record(kinesis, user_watch_log):
    kinesis.put_record(
        StreamName=stream_settings.AWS_KINESIS_STREAM_NAME,
        PartitionKey=get_random_secret_key(),
        Data=encode(user_watch_log)
    )


def encode(user_watch_log):
    return json.dumps(user_watch_log).encode('utf-8')
