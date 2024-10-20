import redis

# Use the endpoint from your AWS ElastiCache
redis_endpoint = 'master.test-cluster.owfnvp.use1.cache.amazonaws.com'

# Connect to Redis
r = redis.StrictRedis(
    host=redis_endpoint,
    port=6379,  # Default Redis port
    password="daisii123456789!",
    ssl=True,  # If encryption in-transit is enabled,
    socket_connect_timeout=10
)

# Test the connection
print(r.ping())  # Should return True if connected