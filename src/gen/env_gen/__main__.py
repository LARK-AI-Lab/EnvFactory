"""Entry point for running env_gen as a module: python -m src.gen.env_gen"""

import asyncio

from src.gen.env_gen.env_gen import main

if __name__ == "__main__":
    asyncio.run(main())
