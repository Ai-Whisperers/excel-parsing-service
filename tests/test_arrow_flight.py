"""
Test Arrow Flight streaming with JSON header
Demonstrates the hybrid architecture: REST control plane + gRPC data plane
"""

import requests
import pyarrow.flight as flight
import json

# Step 1: Upload file and prepare flight (Control Plane - REST)
print("Step 1: Uploading file and preparing Arrow Flight...")
with open('local/dataset/ftth-comentarios.xlsx', 'rb') as f:
    files = {'file': f}
    params = {'flight_id': 'test_ftth_comentarios'}
    response = requests.post(
        'http://localhost:8000/api/v1/flight/upload',
        files=files,
        params=params
    )

print("REST Response (JSON Header):")
flight_info = response.json()
print(json.dumps(flight_info, indent=2))

# Step 2: Connect to Arrow Flight server (Data Plane - gRPC)
print("\nStep 2: Connecting to Arrow Flight server...")
client = flight.FlightClient("grpc://localhost:8815")

# Step 3: Stream data via gRPC
print("\nStep 3: Streaming data via Arrow Flight...")
ticket_str = f"excel:{flight_info['flight_id']}:{{}}"
ticket = flight.Ticket(ticket_str.encode())

reader = client.do_get(ticket)

# Step 4: Process streaming batches
print("\nStep 4: Processing Arrow batches...")
total_rows = 0
batch_count = 0

for batch in reader:
    batch_count += 1
    rows_in_batch = len(batch.data)
    total_rows += rows_in_batch
    print(f"  Batch {batch_count}: {rows_in_batch} rows")

    # Show sample data from first batch
    if batch_count == 1:
        df = batch.data.to_pandas()
        print(f"\n  Sample data (first 3 rows):")
        print(df.head(3).to_string())

print(f"\nTotal: {total_rows} rows streamed across {batch_count} batches")
print(f"Expected: {flight_info['total_records']} rows")
print(f"Match: {total_rows == flight_info['total_records']}")
