# audit README

This service is used to create the audit records in AWS DynamoDB which is a key value store. 

The logging service uses the [Redis list data-types](https://redis.io/docs/data-types/lists/) using [`blpop` blocking pop](https://redis.io/docs/data-types/lists/#blocking-commands) to wait for work and remove it for processing.

This audit queue listens to the keys `journeys` and `transactions` and creates values in respective audit tables in DynamoDB