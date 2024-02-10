Final-project-integrated-transportation-system
Team Members - Surya Rajendran, Dharini Baskaran

Integrated Public Transport System
Overview
The Integrated Public Transport System is a comprehensive project aimed at revolutionizing urban mobility. It proposes an innovative framework to unify various modes of public transportation into a cohesive and user-friendly system. The primary goal is to streamline commuter experiences by enabling a single payment for multiple transport modes within a 90-minute window.

Software Components
1. SQL (Postgres)
Utilized for RFID tag management, fare deduction services, payment calculations, and top-up services.
Advantage: Fully ACID compliant, ensuring data integrity and reliability.
Disadvantage: Lack of options in GUI.
2. Key-Value Store (DynamoDB)
Used for the Transactions database, storing transaction details like transactionId, cardId, amount, transactionType, and timestamps.
Advantage: Designed to scale horizontally, suitable for handling large data and high traffic.
3. Redis MQ (Message Queue)
Incorporates Redis MQ for asynchronous real-time updates across the system.
Calculates fare based on transactionType and zone, updating fare deduction details.
Advantage: In-memory data store allowing fast message processing, critical for the use-case.
Drawback: No message ordering guarantee, which doesn't affect the current use-case.
4. Redis Cache
Enhances system performance by storing frequently used data like busId, fare rates for different zones in-memory.
Advantage: Allows partitioning and sharding for horizontal scaling.
Disadvantage: Limited capacity based on available RAM due to being an in-memory store.
5. REST API (Flask)
Utilized Flask, a Python micro-framework, to implement RESTful APIs for system interaction.
Employs REST endpoints for managing public transport card usage, ensuring modularity and scalability.
6. Containers (Docker and Kubernetes)
Utilizes Docker containers for easy scalability and achieving a modular architecture.
Kubernetes orchestrates containers for reliability and efficient deployment.
Database Management
Utilizes Postgres for relational tables and RFID tag management, ensuring data integrity.
DynamoDB, a NoSQL database, is used for transaction details and journey details for audit purposes due to its scalability.
Redis Cache and Redis Message Queue (MQ) enhance system performance and facilitate real-time updates.
Containers and Orchestration
Docker containers offer scalability and a modular architecture, orchestrated by Kubernetes for efficient deployment.
System Interaction
The system operates with an API-first design approach, ensuring modularity and scalability. The backend services interact through REST endpoints, such as Tag and Top-up, crucial for managing public transport card usage.

Key Functionalities
Payment Mechanism: Users can make a single payment covering diverse transportation modes, encouraging public transport usage.
Real-time Monitoring: Redis-based logging system provides continuous monitoring and analysis of system activities from various sources.
Load Testing and Optimization: Testing conducted using Postman helped identify and resolve latency issues by optimizing database connections.
How to Use
Deployment: Deploy Docker containers using Kubernetes for the Integrated Public Transport System. Build all the images for the services and then deploy using the deploy-all.sh

API Interaction: Access the REST endpoints (Tag, Top-up) to manage public transport card usage.

Logging and Monitoring: Utilize Redis-based logging for continuous system monitoring and analysis.

Load Testing: Ensure system optimization by performing load tests and optimizing database connections.
