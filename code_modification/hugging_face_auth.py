import hashlib, base64, secrets, webbrowser, requests, socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ID of aperture application
CLIENT_ID = "cade646a-c31c-4fea-851b-cc7182172415"

# We have three ports just in case some are already being used
ALLOWED_PORTS = [8000, 8001, 8002]

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        # Get URL parameter for the code
        self.server.auth_code = parse_qs(urlparse(self.path).query).get("code", [None])[0]

        # Send success / show success html message
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Huggingface Login Successful</h1><p>You may return to Aperture</p></body></html>")

    # For silent logs
    def log_message(self, format, *args):
        return


def find_available_port():
    """
    Goes through allowed ports to find an available one
    """

    # Loop through ports, trying to connect
    for port in ALLOWED_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        is_available = sock.connect_ex(("localhost", port)) != 0
        sock.close()
        
        # Return the port if it is available
        if is_available:
            return port
    
    raise Exception(f"No ports from {ALLOWED_PORTS[0]}-{ALLOWED_PORTS[-1]} are free")

def get_token_pipeline():

    # Get port and redirect URI
    port = find_available_port()
    redirect_uri = f"http://localhost:{port}/callback"

    # Generate random verifier for PKCE
    verifier = secrets.token_urlsafe(64)

    # Hash verifier and create PKCE challenge
    verifier_bytes = verifier.encode("utf-8")
    hash_digest = hashlib.sha256(verifier_bytes).digest()
    challenge_base64 = base64.urlsafe_b64encode(hash_digest).decode("utf-8")
    challenge = challenge_base64.rstrip("=")  # (to remove padding)

    # URL parameters for opening HF authorization page
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid profile inference-api",
        "code_challenge": challenge,
        "code_challenge_method": "S256"
    }

    # Open HF authorization page on browser
    webbrowser.open(f"{"https://huggingface.co/oauth/authorize"}?{requests.compat.urlencode(params)}")

    # Catch callback
    server = HTTPServer(("localhost", port), CallbackHandler)
    server.auth_code = None
    server.handle_request()
    
    if not server.auth_code:
        raise Exception("Authorization failed")

    # Get token
    response = requests.post("https://huggingface.co/oauth/token",
        data={"grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code": server.auth_code,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier
    })
    return response.json().get("access_token")