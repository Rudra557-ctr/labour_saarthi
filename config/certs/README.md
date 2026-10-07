# TLS intermediate certificates

## `emSign_SSL_CA_G1.pem`

`censusindia.gov.in` serves **only its leaf certificate** and omits this intermediate CA, so a strict
TLS client cannot build a path to a trusted root and fails with
`unable to get local issuer certificate`.

This file is that missing intermediate, fetched from the CA's own official repository at the URL the
server's certificate itself advertises in its Authority Information Access extension:

```
CA Issuers - URI: http://repository.emsign.com/certs/emSignSSLCAG1.crt
```

- subject: `C=IN, OU=emSign PKI, O=eMudhra Technologies Limited, CN=emSign SSL CA - G1`
- issuer:  `C=IN, OU=emSign PKI, O=eMudhra Technologies Limited, CN=emSign Root CA - G1`

The root is publicly trusted and already present in `certifi`, so appending this intermediate to the
certifi bundle completes the chain and verification **succeeds normally**:

```
$ openssl s_client -connect censusindia.gov.in:443 -CAfile bundle.pem
Verify return code: 0 (ok)
```

**This is not a bypass.** Certificate verification remains fully enabled; we are supplying the
intermediate the server should have sent (standard AIA chasing, which browsers do automatically).
Nothing is disabled, and `verify=False` is used nowhere in this repository.
