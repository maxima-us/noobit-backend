# Implementing new Exchanges

Implementing new Exchanges should be easy. NooBit handles all the logic and only expects you to parse the data to/from NooBit format to Exchange format.

To add a new Exchange REST API:
- Define ExchangeResponseParser (subclassing BaseResponseParser) in `noobit.models.data.response.<exchange>`
- Define ExchangeRequestParser (subclassing BaseRequestParser) in `noobit.models.data.request.<exchange>`
- Define ExchangeRestAPI (sublassing BaseRestAPI) in `noobit.exchanges.<exchange>.rest`
- Add ExchangeRestAPI to `noobit.exchanges.mappings.rest.rest_api_map`. This is used throughout to map exchange names to their respective Rest APIs.

