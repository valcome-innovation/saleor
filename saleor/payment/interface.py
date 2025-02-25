from dataclasses import InitVar, dataclass
from decimal import Decimal
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Union

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]


@dataclass
class PaymentMethodInfo:
    """Uniform way to represent payment method information."""

    first_4: Optional[str] = None
    last_4: Optional[str] = None
    exp_year: Optional[int] = None
    exp_month: Optional[int] = None
    brand: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None


@dataclass
class GatewayResponse:
    """Dataclass for storing gateway response.

    Used for unifying the representation of gateway response.
    It is required to communicate between Saleor and given payment gateway.
    """

    is_success: bool
    action_required: bool
    kind: str  # use "TransactionKind" class
    amount: Decimal
    currency: str
    transaction_id: str
    error: Optional[str]
    customer_id: Optional[str] = None
    payment_method_info: Optional[PaymentMethodInfo] = None
    raw_response: Optional[Dict[str, str]] = None
    action_required_data: Optional[JSONType] = None
    # Some gateway can process transaction asynchronously. This value define if we
    # should create new transaction based on this response
    transaction_already_processed: bool = False
    psp_reference: Optional[str] = None


@dataclass
class AddressData:
    gender: str
    first_name: str
    last_name: str
    company_name: str
    street_address_1: str
    street_address_2: str
    city: str
    city_area: str
    postal_code: str
    country: str
    country_area: str
    phone: str


@dataclass
class PaymentLineData:
    gross: Decimal
    variant_id: int
    product_name: str
    product_sku: str
    quantity: int


@dataclass
class PaymentData:
    """Dataclass for storing all payment information.

    Used for unifying the representation of data.
    It is required to communicate between Saleor and given payment gateway.
    """

    gateway: str
    amount: Decimal
    currency: str
    billing: Optional[AddressData]
    shipping: Optional[AddressData]
    payment_id: int
    graphql_payment_id: str
    order_id: Optional[int]
    customer_ip_address: Optional[str]
    customer_email: str
    token: Optional[str] = None
    customer_id: Optional[str] = None  # stores payment gateway customer ID
    reuse_source: bool = False
    data: Optional[dict] = None
    graphql_customer_id: Optional[str] = None
    refund_data: Optional[Dict[int, int]] = None
    checkout_token: Optional[str] = None
    checkout_metadata: Optional[Dict] = None
    # Optional, lazy-evaluated gateway arguments
    _resolve_lines: InitVar[Callable] = None

    def __post_init__(self, _resolve_lines: Callable):
        self.__resolve_lines = _resolve_lines

    # Note: this field does not appear in webhook payloads,
    # because it's not visible to dataclasses.asdict
    @cached_property
    def lines(self) -> List[PaymentLineData]:
        return self.__resolve_lines()


@dataclass
class TokenConfig:
    """Dataclass for payment gateway token fetching customization."""

    customer_id: Optional[str] = None


@dataclass
class GatewayConfig:
    """Dataclass for storing gateway config data.

    Used for unifying the representation of config data.
    It is required to communicate between Saleor and given payment gateway.
    """

    gateway_name: str
    auto_capture: bool
    supported_currencies: str
    # Each gateway has different connection data so we are not able to create
    # a unified structure
    connection_params: Dict[str, Any]
    store_customer: bool = False
    require_3d_secure: bool = False


@dataclass
class CustomerSource:
    """Dataclass for storing information about stored payment sources in gateways."""

    id: str
    gateway: str
    credit_card_info: Optional[PaymentMethodInfo] = None


@dataclass
class PaymentGateway:
    """Dataclass for storing information about a payment gateway."""

    id: str
    name: str
    currencies: List[str]
    config: List[Dict[str, Any]]


@dataclass
class InitializedPaymentResponse:
    gateway: str
    name: str
    data: Optional[JSONType] = None
