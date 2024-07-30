import os
from dotenv import load_dotenv
import ldap
import ldap.modlist
import requests
import xmltodict

# Load environment variables
load_dotenv()

# Configuration
LDAP_HOST = os.getenv("LDAP_HOST")
LDAP_PORT = int(os.getenv("LDAP_PORT"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN")
LDAP_ADMIN_DN = os.getenv("LDAP_ADMIN_DN")
LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_URL = os.getenv("PLEX_URL")

# Connect to the LDAP server
def connect_ldap():
    ldap_conn = ldap.initialize(f"ldap://{LDAP_HOST}:{LDAP_PORT}")
    ldap_conn.simple_bind_s(LDAP_ADMIN_DN, LDAP_ADMIN_PASSWORD)
    return ldap_conn

def get_plex_users():
    headers = {"X-Plex-Token": PLEX_TOKEN}
    response = requests.get(f"{PLEX_URL}/api/users", headers=headers)
    
    if response.status_code == 200:
        users_xml = xmltodict.parse(response.text)
        return users_xml["MediaContainer"]["User"]
    else:
        print("Failed to retrieve Plex users.")
        return []

def sync_plex_users_to_ldap(ldap_conn, users):
    for user in users:
        username = user["@title"]
        email = user["@email"]
        user_dn = f"cn={username},{LDAP_BASE_DN}"
        
        user_attrs = {
            "objectClass": ["top", "person", "organizationalPerson", "inetOrgPerson"],
            "cn": [username],
            "sn": [username],
            "mail": [email],
        }
        
        try:
            ldap_conn.add_s(user_dn, ldap.modlist.addModlist(user_attrs))
            print(f"Added user: {username}")
        except ldap.ALREADY_EXISTS:
            print(f"User already exists: {username}")

def main():
    ldap_conn = connect_ldap()
    plex_users = get_plex_users()
    sync_plex_users_to_ldap(ldap_conn, plex_users)
    ldap_conn.unbind_s()

if __name__ == "__main__":
    main()