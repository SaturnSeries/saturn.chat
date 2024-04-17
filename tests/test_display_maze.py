import pytest
import httpx
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_maze_endpoint():
    try:
        async with httpx.AsyncClient(base_url='http://localhost:8000') as client:
            logger.info("Making request to '/maze' endpoint...")
            response = await client.get("/maze")
            
            logger.info(f"Response status code: {response.status_code}")

            assert response.status_code == 200

            logger.info("Response body:", response.text)

            maze = response.json()['maze']

            logger.info("Maze structure:", maze)

            assert '+' in maze
            assert '|' in maze
            assert '-' in maze
            assert maze.count('O') == 1
            print("Maze endpoint test passed!")
            print(response.text)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
