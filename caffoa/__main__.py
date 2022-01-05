import logging
import time

from caffoa import execute
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.warning("""
     --- DEPRECATION WARNING ---
    caffoa python package has been deprecated and will no longer receive updates.
    Please check https://github.com/claasd/caffoa.net for a replacement dotnet tool
    --- DEPRECATION WARNING ---
    """)

    time.sleep(5.0)
    execute()
    logging.warning("""
     --- DEPRECATION WARNING ---
    caffoa python package has been deprecated and will no longer receive updates.
    Please check https://github.com/claasd/caffoa.net for a replacement dotnet tool
    --- DEPRECATION WARNING ---
    """)

    time.sleep(5.0)
