import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkcnlhZC10ZXN0LXVzZXIiLCJ1c2VySWQiOiJkcnlhZC10ZXN0LXVzZXIiLCJlbWFpbCI6ImRyeWFkdGVzdEByZWhyaWcuY29tIiwidXNlcm5hbWUiOiJkcnlhZHRlc3QiLCJyb2xlIjoiYWRtaW4iLCJkZXBhcnRtZW50IjoiSVQgU3VwcG9ydCIsImlhdCI6MTc1OTY3NjYyNiwiZXhwIjoxNzU5NzYzMDI2LCJhdWQiOiJyYWRhci1wbGF0Zm9ybSIsImlzcyI6InJhZGFyLWF1dGgtc2VydmljZSJ9.lK3XURIgxG6RFehzhAYSZpNMawmAD6fqRaSOWgYAG6Y"

payload = jwt.decode(token, options={'verify_signature': False})

print("Token Payload:")
print(f"  iat: {payload['iat']}")
print(f"  exp: {payload['exp']}")
print(f"  Duration: {payload['exp'] - payload['iat']} seconds")
print(f"  Duration: {(payload['exp'] - payload['iat']) / 3600} hours")

