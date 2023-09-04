# Cloudflare Reverse DNS [![Hippocratic License HL3-FULL](https://img.shields.io/static/v1?label=Hippocratic%20License&message=HL3-FULL&labelColor=5e2751&color=bc8c3d)](https://firstdonoharm.dev/version/3/0/full.html)

> Service to keep a local IP address reverse DNS record up to date on Cloudflare.

## Usage

The script expects the following environment variables to be set:

```sh
CF_API_TOKEN=your_token_from_cloudflare
CF_ACCOUNT_ID=your_cloudfare_account_id
CF_ZONE_ID=your_cloudflare_zone_id
CF_RECORD_NAME=your.domain.here
```

See `secret.example.env` for an example.

Once set, then run `python3 src/cloudfare_rdns.py` to start the service.
