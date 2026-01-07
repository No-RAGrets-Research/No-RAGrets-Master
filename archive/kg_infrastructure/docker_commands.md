# DGraph Setup Commands

## Start DGraph Database

docker run --rm -it -p 8080:8080 -p 9080:9080 dgraph/standalone:latest

- Port 8080: HTTP/GraphQL endpoint
- Port 9080: gRPC endpoint

## Start Ratel UI (optional)

docker run --rm -it -p 8000:8000 dgraph/ratel:latest

- Port 8000: Web-based DGraph dashboard
- Connect to: localhost:8080

## Access Points

- Ratel Dashboard: http://localhost:8000
- GraphQL Playground: http://localhost:8080/graphql
- Health Check: http://localhost:8080/health
