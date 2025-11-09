from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

private_key = ec.generate_private_key(ec.SECP256R1())
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)
public_key = private_key.public_key()
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
private_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode('utf-8')
public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b'=')

print("VAPID Private Key:", private_b64)
print("VAPID Public Key:", public_b64)