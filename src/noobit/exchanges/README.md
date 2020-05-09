# Implementing new Exchanges

Implementing new Exchanges should be easy. This is why NooBit is designed in such a way that you do not need to worry about the logic and only need to parse the data to/from NooBit format to Exchange format.

To add a new Exchange REST API:
- Define <Exchange>ResponseParser (subclassing BaseResponseParser) in `noobit.models.data.response.<exchange>`
- Define <Exchange>RequestParser (subclassing BaseRequestParser) in `noobit.models.data.request.<exchange>`
- Define <Exchange>RestAPI (sublassing BaseRestAPI) in noobit.exchanges.<exchange>.rest
- Add <Exchange>RestAPI to noobit.exchanges.mappings.rest.rest_api_map. This is used throughout to map exchange names to their respective Rest APIs.

