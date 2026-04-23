"""
Script to add sample data to MongoDB database
Run: python add_sample_data.py
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Users
SAMPLE_USERS = [
    {
        "email": "john@example.com",
        "full_name": "John Smith",
        "password": "Password123!",  # Will be hashed
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "sarah@example.com",
        "full_name": "Sarah Johnson",
        "password": "SecurePass456!",
        "is_active": True,
        "is_superuser": False,
    },
    {
        "email": "mike@example.com",
        "full_name": "Mike Williams",
        "password": "AdminPass789!",
        "is_active": True,
        "is_superuser": True,  # Admin user
    },
    {
        "email": "emma@example.com",
        "full_name": "Emma Brown",
        "password": "Emma2025@",
        "is_active": True,
        "is_superuser": False,
    },
]

# Sample Articles
SAMPLE_ARTICLES = [
    {
        "slug": "getting-started-with-machine-learning",
        "title": "Getting Started with Machine Learning",
        "author": "John Smith",
        "authorEmail": "john@example.com",
        "authorId": None,  # Will be set after user creation
        "category": "AI & ML",
        "tags": ["machine-learning", "ai", "python", "beginner"],
        "readingTime": "5 min read",
        "featuredImage": "https://images.unsplash.com/photo-1677442d019cecf9d6f67af76bde80037d669ee01?w=800",
        "shortDescription": "Learn the fundamentals of machine learning and get started with your first ML project.",
        "content": """
# Getting Started with Machine Learning

Machine learning is one of the most exciting fields in technology today. In this article, we'll explore the basics of ML and help you get started.

## What is Machine Learning?

Machine Learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. Instead of following pre-programmed rules, ML systems learn patterns from data and improve their performance over time.

## Key Concepts

### 1. Supervised Learning
In supervised learning, we have labeled training data. The model learns from input-output pairs and can predict outputs for new inputs.

### 2. Unsupervised Learning
Unsupervised learning works with unlabeled data. The model tries to find patterns or structure in the data without predefined categories.

### 3. Reinforcement Learning
The model learns by interacting with an environment, receiving rewards or penalties for its actions.

## Getting Your First ML Model Running

Here's a simple example using Python and scikit-learn:

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load data
iris = load_iris()
X, y = iris.data, iris.target

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")
```

## Best Practices

1. **Start with clean data** - Data quality is crucial
2. **Understand your data** - Explore and visualize before modeling
3. **Split your data** - Always use train/test split
4. **Evaluate properly** - Use appropriate metrics for your problem
5. **Iterate and improve** - ML is iterative

## Next Steps

- Learn Python fundamentals
- Study linear algebra and statistics
- Try Kaggle competitions
- Build projects

Happy learning!
        """.strip(),
        "status": "approved",
        "isFeatured": True,
        "viewCount": 245,
        "likesCount": 18,
        "likes": [],
        "created_at": datetime.utcnow() - timedelta(days=10),
        "updated_at": datetime.utcnow() - timedelta(days=10),
    },
    {
        "slug": "web-development-best-practices",
        "title": "Web Development Best Practices in 2025",
        "author": "Sarah Johnson",
        "authorEmail": "sarah@example.com",
        "authorId": None,
        "category": "Web Development",
        "tags": ["web-dev", "best-practices", "react", "performance"],
        "readingTime": "8 min read",
        "featuredImage": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800",
        "shortDescription": "Discover the latest best practices for modern web development in 2025.",
        "content": """
# Web Development Best Practices in 2025

The web development landscape continues to evolve rapidly. Here are the best practices you should follow in 2025.

## Performance Optimization

### 1. Core Web Vitals
Focus on three key metrics:
- **Largest Contentful Paint (LCP)**: < 2.5 seconds
- **First Input Delay (FID)**: < 100 milliseconds
- **Cumulative Layout Shift (CLS)**: < 0.1

### 2. Image Optimization
- Use modern formats (WebP, AVIF)
- Implement lazy loading
- Responsive images with srcset

### 3. Code Splitting
Split your JavaScript bundles to load only what users need.

## Security Best Practices

### 1. Content Security Policy (CSP)
Implement strict CSP headers to prevent XSS attacks.

### 2. HTTPS Everywhere
Always use HTTPS, even in development.

### 3. Input Validation
Never trust user input. Always validate and sanitize.

## Frontend Frameworks

### React
- Use functional components and hooks
- Implement proper error boundaries
- Optimize re-renders with React.memo

### Vue
- Leverage composition API
- Use script setup for cleaner components

### Svelte
- Build highly optimized applications
- Smaller bundle sizes

## Backend Considerations

- Use environment variables for secrets
- Implement proper logging
- Use database indexes
- Rate limiting and throttling
- API versioning

## Testing

- Write unit tests (Jest, Vitest)
- Integration tests (Testing Library)
- E2E tests (Cypress, Playwright)
- Aim for 80%+ code coverage

## Accessibility

- Use semantic HTML
- Ensure keyboard navigation
- Use proper ARIA labels
- Test with screen readers

## Deployment

- Use CI/CD pipelines
- Automated testing before deployment
- Blue-green deployments
- Monitor performance metrics

## Conclusion

Following these practices will help you build better, faster, and more secure web applications!
        """.strip(),
        "status": "approved",
        "isFeatured": False,
        "viewCount": 512,
        "likesCount": 42,
        "likes": [],
        "created_at": datetime.utcnow() - timedelta(days=7),
        "updated_at": datetime.utcnow() - timedelta(days=7),
    },
    {
        "slug": "python-async-programming-guide",
        "title": "Complete Guide to Async Programming in Python",
        "author": "Mike Williams",
        "authorEmail": "mike@example.com",
        "authorId": None,
        "category": "Python",
        "tags": ["python", "async", "asyncio", "concurrency"],
        "readingTime": "10 min read",
        "featuredImage": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800",
        "shortDescription": "Master asynchronous programming in Python and build high-performance applications.",
        "content": """
# Complete Guide to Async Programming in Python

Asynchronous programming is essential for building scalable applications. Let's dive deep into Python's async ecosystem.

## What is Async Programming?

Async programming allows your code to handle multiple operations concurrently without blocking. It's perfect for I/O-bound operations like network requests and database queries.

## asyncio Basics

### Coroutines
Coroutines are functions defined with `async def`:

```python
import asyncio

async def greet(name):
    print(f"Hello {name}!")
    await asyncio.sleep(1)
    print(f"Goodbye {name}!")

# Run coroutine
asyncio.run(greet("Alice"))
```

### Tasks
Tasks are wrappers around coroutines:

```python
async def main():
    task1 = asyncio.create_task(greet("Alice"))
    task2 = asyncio.create_task(greet("Bob"))
    
    await asyncio.gather(task1, task2)

asyncio.run(main())
```

## Common Patterns

### 1. Gathering Tasks
Run multiple tasks concurrently:

```python
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3),
)
```

### 2. Error Handling
Handle errors in async code:

```python
try:
    result = await asyncio.wait_for(fetch_data(), timeout=5)
except asyncio.TimeoutError:
    print("Request timed out!")
```

### 3. Async Context Managers
Use context managers with async:

```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
```

## Common Libraries

### aiohttp
Async HTTP client:

```python
import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()
```

### asyncpg
Async PostgreSQL driver:

```python
import asyncpg

conn = await asyncpg.connect('user:password@localhost/db')
rows = await conn.fetch('SELECT * FROM users')
```

### motor
Async MongoDB driver (used in our blog!):

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient()
db = client.database_name
```

## Performance Tips

1. Avoid blocking operations
2. Use connection pools
3. Implement proper error handling
4. Monitor event loop
5. Use profiling tools

## Conclusion

Async programming is powerful but requires careful handling. Start simple and gradually increase complexity!
        """.strip(),
        "status": "approved",
        "isFeatured": True,
        "viewCount": 378,
        "likesCount": 31,
        "likes": [],
        "created_at": datetime.utcnow() - timedelta(days=5),
        "updated_at": datetime.utcnow() - timedelta(days=5),
    },
    {
        "slug": "database-optimization-techniques",
        "title": "Database Optimization Techniques",
        "author": "Emma Brown",
        "authorEmail": "emma@example.com",
        "authorId": None,
        "category": "Backend",
        "tags": ["database", "optimization", "sql", "mongodb"],
        "readingTime": "7 min read",
        "featuredImage": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "shortDescription": "Learn essential database optimization techniques to improve application performance.",
        "content": """
# Database Optimization Techniques

Database performance is critical for application success. Here are the techniques you need to know.

## Indexing

### Single Field Indexes
```sql
CREATE INDEX idx_email ON users(email);
```

### Compound Indexes
```sql
CREATE INDEX idx_user_status ON posts(user_id, status);
```

### Index Considerations
- Index frequently queried fields
- Don't over-index
- Monitor index usage
- Rebuild indexes periodically

## Query Optimization

### 1. Use EXPLAIN
Analyze query performance:
```sql
EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';
```

### 2. Avoid N+1 Queries
Bad:
```python
users = User.find_all()
for user in users:
    posts = Post.find_by_user(user.id)  # N queries!
```

Good:
```python
users = User.with_posts().find_all()  # 1 query with JOIN
```

### 3. Select Only Needed Columns
Bad:
```sql
SELECT * FROM users;
```

Good:
```sql
SELECT id, name, email FROM users;
```

## Connection Pooling

Reuse database connections:

```python
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:pass@localhost/db',
    pool_size=20,
    max_overflow=40
)
```

## Caching

### Query Result Caching
```python
import redis

cache = redis.Redis()

def get_user(user_id):
    key = f"user:{user_id}"
    cached = cache.get(key)
    
    if cached:
        return json.loads(cached)
    
    user = db.get_user(user_id)
    cache.setex(key, 3600, json.dumps(user))
    return user
```

### MongoDB Indexing
```javascript
db.articles.createIndex({ slug: 1 });
db.articles.createIndex({ category: 1 });
db.articles.createIndex({ created_at: -1 });
```

## Database-Specific Tips

### MongoDB
- Use aggregation pipeline for complex queries
- Denormalize strategically
- Monitor oplog

### PostgreSQL
- Use VACUUM regularly
- Partition large tables
- Analyze query plans

### Redis
- Use appropriate data structures
- Set expiration times
- Monitor memory usage

## Monitoring

- Track slow queries
- Monitor CPU and memory
- Alert on anomalies
- Regular backups

## Conclusion

Database optimization is an ongoing process. Regular monitoring and adjustment keep your applications fast!
        """.strip(),
        "status": "approved",
        "isFeatured": False,
        "viewCount": 289,
        "likesCount": 22,
        "likes": [],
        "created_at": datetime.utcnow() - timedelta(days=3),
        "updated_at": datetime.utcnow() - timedelta(days=3),
    },
    {
        "slug": "cloud-deployment-strategies",
        "title": "Cloud Deployment Strategies for Modern Apps",
        "author": "John Smith",
        "authorEmail": "john@example.com",
        "authorId": None,
        "category": "DevOps",
        "tags": ["cloud", "deployment", "docker", "kubernetes"],
        "readingTime": "9 min read",
        "featuredImage": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800",
        "shortDescription": "Explore modern cloud deployment strategies for reliable and scalable applications.",
        "content": """
# Cloud Deployment Strategies for Modern Apps

Cloud deployment requires careful planning. Here are the strategies and best practices.

## Deployment Approaches

### 1. Monolithic Deployment
- Single large application
- Simple to start
- Harder to scale
- Less resilient

### 2. Microservices Deployment
- Multiple small services
- Independent scaling
- Complex management
- Better resilience

### 3. Serverless Deployment
- No server management
- Pay per execution
- Cold start issues
- Perfect for event-driven apps

## Container Strategies

### Docker
Package applications consistently:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "app.main:app"]
```

### Kubernetes
Orchestrate containers at scale:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myrepo/api:latest
        ports:
        - containerPort: 8000
```

## Cloud Providers

### AWS
- EC2: Virtual servers
- RDS: Managed databases
- Lambda: Serverless functions
- S3: Object storage

### Google Cloud
- Compute Engine: Virtual machines
- Cloud SQL: Managed databases
- Cloud Functions: Serverless
- Cloud Storage: Object storage

### Azure
- Virtual Machines
- App Service
- Functions
- Cosmos DB

## CI/CD Pipelines

### GitHub Actions
```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: docker build -t app .
      - run: docker push myrepo/app
```

## Database Strategies

### Read Replicas
Improve read performance with replicas

### Database Sharding
Split data across multiple databases

### Backup Strategies
- Automated daily backups
- Point-in-time recovery
- Test restores regularly

## Monitoring and Logging

- Centralized logging (ELK, Splunk)
- Distributed tracing (Jaeger, Zipkin)
- Application monitoring (New Relic, DataDog)
- Alerting on key metrics

## Scaling Strategies

### Horizontal Scaling
Add more instances:
- Load balancing
- Session management
- Database replication

### Vertical Scaling
Increase instance resources:
- Limited by instance size
- Requires restart
- Simpler initially

## Security in Cloud

- Use managed services
- Encrypt in transit and at rest
- Regular security audits
- Principle of least privilege

## Cost Optimization

- Reserved instances
- Spot instances
- Auto-scaling
- Monitor unused resources

## Conclusion

Choose deployment strategies based on your application needs. Start simple and evolve!
        """.strip(),
        "status": "approved",
        "isFeatured": False,
        "viewCount": 198,
        "likesCount": 15,
        "likes": [],
        "created_at": datetime.utcnow() - timedelta(days=2),
        "updated_at": datetime.utcnow() - timedelta(days=2),
    },
]


async def add_sample_data():
    """Add sample data to MongoDB"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.mongo_uri)
        db = client[settings.db_name]
        
        logger.info("Connected to MongoDB")
        
        # Check if data already exists
        existing_users = await db[settings.users_collection].count_documents({})
        if existing_users > 0:
            logger.warning(f"Database already contains {existing_users} users. Skipping insertion.")
            return
        
        # 1. Add Users
        logger.info("Adding sample users...")
        users_data = []
        user_id_map = {}  # Map email to user_id
        
        for user in SAMPLE_USERS:
            user_doc = {
                "email": user["email"],
                "full_name": user["full_name"],
                "hashed_password": get_password_hash(user["password"]),
                "is_active": user["is_active"],
                "is_superuser": user["is_superuser"],
                "created_at": datetime.utcnow(),
            }
            users_data.append(user_doc)
        
        result = await db[settings.users_collection].insert_many(users_data)
        logger.info(f"✅ Added {len(result.inserted_ids)} users")
        
        # Create mapping of email to user IDs
        users = await db[settings.users_collection].find({}).to_list(None)
        for user in users:
            user_id_map[user["email"]] = str(user["_id"])
        
        # 2. Add Articles
        logger.info("Adding sample articles...")
        articles_data = []
        
        for article in SAMPLE_ARTICLES:
            author_email = article["authorEmail"]
            article_doc = {
                **article,
                "authorId": user_id_map.get(author_email),  # Set the actual user ID
            }
            articles_data.append(article_doc)
        
        result = await db[settings.articles_collection].insert_many(articles_data)
        logger.info(f"✅ Added {len(result.inserted_ids)} articles")
        
        # 3. Create Indexes
        logger.info("Creating indexes...")
        await db[settings.articles_collection].create_index("slug", unique=True)
        await db[settings.articles_collection].create_index("category")
        await db[settings.articles_collection].create_index("isFeatured")
        await db[settings.users_collection].create_index("email", unique=True)
        logger.info("✅ Indexes created")
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("SAMPLE DATA ADDED SUCCESSFULLY!")
        logger.info("="*50)
        logger.info("\n📧 Sample Users (use these to login):")
        for user in SAMPLE_USERS:
            admin_badge = " (ADMIN)" if user["is_superuser"] else ""
            logger.info(f"  Email: {user['email']}{admin_badge}")
            logger.info(f"  Password: {user['password']}\n")
        
        logger.info(f"\n📰 Added {len(articles_data)} sample articles")
        logger.info("\nYou can now:")
        logger.info("  1. Login with any of the sample user accounts")
        logger.info("  2. View articles on the home page")
        logger.info("  3. Try all features\n")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Error adding sample data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(add_sample_data())
