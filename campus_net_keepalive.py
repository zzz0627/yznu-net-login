import json
import logging
import os
import platform
import subprocess
import sys
import time
from typing import Dict, List, Optional

import requests


# Global configuration loaded from config.json
config: Dict = {}
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.json") -> Dict:
    """Loads configuration from JSON file.
    
    Args:
        config_path: Path to configuration file.
    
    Returns:
        Configuration dictionary.
    
    Raises:
        FileNotFoundError: If config file doesn't exist.
        json.JSONDecodeError: If config file is malformed.
        ValueError: If required fields are missing.
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please copy config.json.example to config.json and fill in your credentials")
        raise FileNotFoundError(f"Missing {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {config_path}: {e}")
        raise
    
    # Validate required fields
    required = ['username', 'password', 'login_url']
    missing = [field for field in required if not cfg.get(field)]
    if missing:
        logger.error(f"Missing required fields in config: {', '.join(missing)}")
        raise ValueError(f"Incomplete configuration: {missing}")
    
    # Check for placeholder values
    if cfg['username'] == 'your_student_id' or cfg['password'] == 'your_password':
        logger.error("Configuration contains placeholder values")
        logger.error("Please edit config.json with your actual credentials")
        raise ValueError("Placeholder values in configuration")
    
    logger.info("Configuration loaded successfully")
    return cfg


def setup_logging(level: str = "INFO") -> None:
    """Configures logging format and level.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def rc4_encrypt(plaintext: str, key: str) -> str:
    """Encrypts password using RC4 algorithm.
    
    Implements the RC4 stream cipher (KSA + PRGA) as used by the
    campus gateway's JavaScript authentication system.
    
    Args:
        plaintext: Password in plain text.
        key: Encryption key (millisecond timestamp as string).
    
    Returns:
        Hex-encoded encrypted string.
    """
    plaintext = plaintext.strip()
    key = str(key)
    
    plen = len(key)
    size = len(plaintext)
    
    # Initialize key array and S-box
    key_array = [0] * 256
    sbox = [0] * 256
    output = []
    
    # KSA (Key-Scheduling Algorithm)
    for i in range(256):
        key_array[i] = ord(key[i % plen])
        sbox[i] = i
    
    j = 0
    for i in range(256):
        j = (j + sbox[i] + key_array[i]) % 256
        sbox[i], sbox[j] = sbox[j], sbox[i]
    
    # PRGA (Pseudo-Random Generation Algorithm)
    a = b = 0
    for i in range(size):
        a = (a + 1) % 256
        b = (b + sbox[a]) % 256
        sbox[a], sbox[b] = sbox[b], sbox[a]
        c = (sbox[a] + sbox[b]) % 256
        
        # XOR and convert to hex
        temp = ord(plaintext[i]) ^ sbox[c]
        output.append(format(temp, '02x'))
    
    return ''.join(output)


def ping_dns(host: str, timeout: int) -> bool:
    """Tests DNS server reachability via ICMP ping.
    
    Args:
        host: DNS server IP address.
        timeout: Ping timeout in seconds.
    
    Returns:
        True if ping succeeds, False otherwise.
    """
    try:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), host]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1
        )
        
        return result.returncode == 0
    
    except (subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"DNS ping to {host} failed: {e}")
        return False


def check_network_http(url: str, timeout: int, user_agent: str) -> bool:
    """Checks internet connectivity via HTTP request.
    
    Detects campus network hijacking by examining response URL.
    The campus gateway redirects all HTTP traffic to its login portal
    (1.1.1.3/ac_portal/*) when authentication is required.
    
    Args:
        url: URL to test (e.g., http://www.baidu.com).
        timeout: Request timeout in seconds.
        user_agent: User-Agent header value.
    
    Returns:
        True if genuine internet access, False if hijacked or unreachable.
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={'User-Agent': user_agent},
            allow_redirects=True
        )
        
        if response.status_code != 200:
            logger.debug(f"HTTP check failed: status {response.status_code}")
            return False
        
        # Detect campus portal hijacking
        final_url = response.url.lower()
        if '1.1.1.3' in final_url or 'ac_portal' in final_url:
            logger.debug(f"HTTP hijacked to campus portal: {response.url}")
            return False
        
        # Verify no suspicious redirects
        if response.history and 'baidu.com' not in final_url:
            logger.debug(f"Unexpected redirect: {url} -> {response.url}")
            return False
        
        logger.debug(f"HTTP check passed: {response.url}")
        return True
    
    except requests.exceptions.Timeout:
        logger.debug(f"HTTP request to {url} timed out")
        return False
    
    except requests.exceptions.ConnectionError as e:
        logger.debug(f"HTTP connection to {url} failed: {e}")
        return False
    
    except Exception as e:
        logger.debug(f"HTTP check error: {e}")
        return False


def check_network() -> bool:
    """Performs dual-mode network connectivity check.
    
    Attempts DNS ping first (fast), falls back to HTTP check if needed.
    
    Returns:
        True if internet accessible, False otherwise.
    """
    # Priority 1: DNS ping
    dns_servers = config.get('dns_servers', ['223.5.5.5', '8.8.8.8'])
    dns_timeout = config.get('dns_timeout', 3)
    
    for dns in dns_servers:
        if ping_dns(dns, dns_timeout):
            logger.debug(f"DNS ping to {dns} succeeded")
            return True
    
    logger.debug("All DNS pings failed, trying HTTP check")
    
    # Priority 2: HTTP check
    http_url = config.get('http_check_url', 'http://www.baidu.com')
    http_timeout = config.get('http_timeout', 5)
    user_agent = config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    
    if check_network_http(http_url, http_timeout, user_agent):
        logger.debug("HTTP check succeeded")
        return True
    
    logger.warning("Network check failed: disconnected")
    return False


def login(username: str, password: str, login_url: str) -> bool:
    """Authenticates user against campus network gateway.
    
    Workflow:
        1. Generate millisecond timestamp as encryption key
        2. Encrypt password with RC4
        3. Build POST payload
        4. Send authentication request
        5. Parse JSON response
    
    Args:
        username: Student ID or username.
        password: Account password (will be encrypted).
        login_url: Gateway login endpoint.
    
    Returns:
        True if authentication successful, False otherwise.
    """
    try:
        # Generate timestamp key (13-digit milliseconds)
        auth_tag = str(int(time.time() * 1000))
        
        # Encrypt password with RC4
        encrypted_pwd = rc4_encrypt(password, auth_tag)
        
        # Build POST payload
        payload = {
            'opr': 'pwdLogin',
            'userName': username,
            'pwd': encrypted_pwd,
            'auth_tag': auth_tag,
            'rememberPwd': '0'
        }
        
        # Prepare headers
        headers = {
            'User-Agent': config.get('user_agent', 'Mozilla/5.0'),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://1.1.1.3/ac_portal/disclaimer/pc.html'
        }
        
        logger.info(f"Attempting login for user: {username}")
        
        response = requests.post(
            login_url,
            data=payload,
            headers=headers,
            timeout=10
        )
        
        # Parse response
        if response.status_code != 200:
            logger.error(f"Login failed: HTTP {response.status_code}")
            return False
        
        try:
            result = response.json()
            
            if result.get('success'):
                logger.info(f"✓ Login successful for user: {username}")
                return True
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"✗ Login failed: {error_msg}")
                return False
        
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text[:200]}")
            return False
    
    except requests.exceptions.Timeout:
        logger.error("Login request timed out")
        return False
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error during login: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected login error: {e}")
        return False


def login_with_retry(username: str, password: str, login_url: str) -> bool:
    """Retries login with exponential backoff on failure.
    
    Implements backoff sequence: 5s, 10s, 20s, 40s, 60s (capped).
    
    Args:
        username: Student ID.
        password: Password.
        login_url: Gateway endpoint.
    
    Returns:
        True if any attempt succeeds, False if all fail.
    """
    max_retry = config.get('max_retry', 5)
    base_delay = config.get('retry_base_delay', 5)
    backoff_factor = config.get('retry_backoff_factor', 2)
    
    for attempt in range(1, max_retry + 1):
        logger.info(f"Login attempt {attempt}/{max_retry}")
        
        if login(username, password, login_url):
            logger.info("Login succeeded, network restored")
            return True
        
        if attempt < max_retry:
            delay = min(base_delay * (backoff_factor ** (attempt - 1)), 60)
            logger.warning(f"Login failed, retrying in {delay}s...")
            time.sleep(delay)
        else:
            logger.error(f"All {max_retry} login attempts failed")
    
    return False


def main() -> None:
    """Main daemon loop: monitors network and re-authenticates on disconnect."""
    global config
    
    # Load configuration
    try:
        config = load_config()
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        sys.exit(1)
    
    # Setup logging
    log_level = config.get('log_level', 'INFO')
    setup_logging(log_level)
    
    # Extract credentials
    username = config['username']
    password = config['password']
    login_url = config['login_url']
    check_interval = config.get('check_interval', 60)
    
    # Print startup banner
    logger.info("=" * 60)
    logger.info("Campus Network Auto-Login Daemon Started")
    logger.info(f"Username: {username}")
    logger.info(f"Check interval: {check_interval}s")
    logger.info(f"Login endpoint: {login_url}")
    logger.info("=" * 60)
    
    consecutive_failures = 0
    
    while True:
        try:
            # Check network status
            if check_network():
                if consecutive_failures > 0:
                    logger.info(f"Network restored (was down {consecutive_failures} times)")
                    consecutive_failures = 0
                else:
                    logger.debug("Network status: OK")
            else:
                consecutive_failures += 1
                logger.warning(f"Network disconnected (failure #{consecutive_failures})")
                
                # Trigger login
                if login_with_retry(username, password, login_url):
                    consecutive_failures = 0
                else:
                    logger.error("Login failed, will retry on next check")
            
            # Sleep until next check
            time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("\nReceived interrupt signal, shutting down...")
            break
        
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            logger.info("Recovering in 5s...")
            time.sleep(5)
    
    logger.info("Campus Network Auto-Login Daemon Stopped")


if __name__ == "__main__":
    main()