from paypalcheckoutsdk.core import PayPalHttpClient, PayPalEnvironment


def get_paypal_client(**connection_params):
    """Set up and return PayPal Python SDK environment with PayPal access credentials.

    This sample uses SandboxEnvironment. In production, use LiveEnvironment.
    """
    client_id = connection_params.get("client_id")
    private_key = connection_params.get("private_key")
    sandbox_mode = connection_params.get("sandbox_mode")
    api_url = "https://api-m.sandbox.paypal.com" if sandbox_mode else "https://api-m.paypal.com"
    web_url = "https://www.sandbox.paypal.com" if sandbox_mode else "https://www.paypal.com"

    environment = PayPalEnvironment(
        client_id=client_id,
        client_secret=private_key,
        apiUrl=api_url,
        webUrl=web_url
    )

    """Returns PayPal HTTP client instance with environment that has access
    credentials context. Use this instance to invoke PayPal APIs, provided the
    credentials have access. """
    return PayPalHttpClient(environment)
