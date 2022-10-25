pytest_plugins = [
    "saleor.tests.fixtures",
    "saleor.plugins.tests.fixtures",
    "saleor.graphql.tests.fixtures",
    "saleor.graphql.channel.tests.fixtures",
    "saleor.graphql.account.tests.benchmark.fixtures",
    "saleor.graphql.order.tests.benchmark.fixtures",
    "saleor.graphql.product.tickets.tests.fixtures",
    "saleor.payment.gateways.paypal.tests.fixtures",  # VALCOME
    "saleor.payment.gateways.sofort.tests.fixtures",  # VALCOME
]
