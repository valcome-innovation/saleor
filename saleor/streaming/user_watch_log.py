import boto3
import graphene
import json
import boto3.exceptions
import logging

from django.core.management.utils import get_random_secret_key
from .stream_ticket import determine_ticket_type, get_stream_meta
from ..streaming import stream_settings
from ..order.models import Order

logger = logging.getLogger(__name__)


def create_user_watch_log_from_order(order: "Order"):
    (game_id, season_id, expires, start_time, team_ids, league_ids) = get_stream_meta(order)
    ticket_type = determine_ticket_type(game_id, season_id, expires)
    access_type = determine_watch_access_type(ticket_type, team_ids, start_time, expires)
    print(access_type)
    send_user_watch_log_to_kinesis_stream_silent(order.user, game_id, access_type)


def determine_watch_access_type(ticket_type, team_ids, start_time, expires):
    if team_ids is not None:
        if ticket_type == "season":
            return "season_team"
        elif ticket_type == "timed":
            print(start_time)
            print(expires)
            if start_time == expires:
                return "day"
            else:
                return "month_team"


def send_user_watch_log_to_kinesis_stream_silent(user, game_id, ticket_type):
    try:
        send_user_watch_log_to_kinesis_stream(user, game_id, ticket_type)
    except Exception as exc:
        logger.exception(
            f"[AWS Kinesis] Couldn't create user watch log user_id={user.id}, "
            f"game_id={game_id}, type={ticket_type}",
            exc_info=exc
        )


def send_user_watch_log_to_kinesis_stream(user, game_id, ticket_type):
    credentials = retrieve_cognito_credentials()
    kinesis = create_kinesis_client(credentials)
    user_watch_log = create_user_watch_log(user.id, game_id, ticket_type)
    put_stream_record(kinesis, user_watch_log)


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


def create_user_watch_log(user_id: str, game_id: str, ticket_type: str):
    global_user_id = graphene.Node.to_global_id("User", user_id)
    return {
        'id': f'{game_id}_{global_user_id}',
        'gameId': f'{game_id}',
        'userId': f'{global_user_id}',
        'type': f'{ticket_type}',
        'watchDuration': 0
    }


def put_stream_record(kinesis, user_watch_log):
    kinesis.put_record(
        StreamName=stream_settings.AWS_KINESIS_STREAM_NAME,
        PartitionKey=get_random_secret_key(),
        Data=encode(user_watch_log)
    )


def encode(user_watch_log):
    return json.dumps(user_watch_log).encode('utf-8')
